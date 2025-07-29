# license_analyzer/core.py
"""
License Analyzer Module

A robust Python module for analyzing and comparing software licenses using
multiple matching strategies including SHA256, fingerprinting, and semantic embeddings.
"""

import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, List, Tuple, Optional, Union, Set, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from appdirs import user_cache_dir


class MatchMethod(Enum):
    """Enumeration of available matching methods."""

    SHA256 = "sha256"
    FINGERPRINT = "fingerprint"
    EMBEDDING = "embedding"


@dataclass
class LicenseMatch:
    """Represents a license match result."""

    name: str
    score: float
    method: MatchMethod

    def __post_init__(self):
        """Validate score range."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {self.score}")


@dataclass
class DatabaseEntry:
    """Represents a license database entry."""

    name: str
    sha256: str
    fingerprint: str
    embedding: Optional[List[float]] = None
    updated: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    file_path: Optional[Path] = None


class LicenseDatabase:
    """Manages the license database with lazy loading and caching."""

    def __init__(
        self,
        spdx_dir: Path,
        cache_dir: Path,
        embedding_model_name: str = "all-MiniLM-L6-v2",
    ):
        self.spdx_dir = Path(spdx_dir)
        self.cache_dir = Path(cache_dir)  # This is for internal database JSONs
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.embedding_model_name = embedding_model_name
        self._embedding_model = None

        self.licenses_db_path = self.cache_dir / "licenses.json"

        self._licenses_db: Optional[Dict[str, DatabaseEntry]] = None

        self.logger = logging.getLogger(__name__)

    @property
    def embedding_model(self):
        """Lazy load the embedding model only when needed."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self.logger.info(
                    f"Loading embedding model: {self.embedding_model_name} (first time, may download)..."
                )
                # SentenceTransformer automatically logs download progress to the logger configured by RichHandler
                self._embedding_model = SentenceTransformer(self.embedding_model_name)
                self.logger.info(f"Loaded embedding model: {self.embedding_model_name}")
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for embedding-based matching. Please install it with pip install sentence-transformers"
                )
        return self._embedding_model

    def _sha256sum(self, path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def _sha256sum_text(self, text: str) -> str:
        """Calculate SHA256 hash of text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent processing."""
        return " ".join(text.lower().split())

    def _canonical_fingerprint(self, text: str) -> str:
        """Generate canonical fingerprint from text."""
        tokens = sorted(set(self._normalize_text(text).split()))
        return hashlib.sha256(" ".join(tokens).encode("utf-8")).hexdigest()

    def _load_existing_db(self, db_path: Path) -> Dict[str, dict]:
        """Load existing database from JSON file."""
        if not db_path.exists():
            return {}

        try:
            with open(db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self.logger.warning(f"Failed to load database {db_path}: {e}")
            return {}

    def _save_db(self, db: Dict[str, dict], db_path: Path) -> None:
        """Save database to JSON file."""
        try:
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2, ensure_ascii=False)
        except IOError as e:
            self.logger.error(f"Failed to save database {db_path}: {e}")
            raise

    def _update_database(
        self,
        source_dir: Path,
        db_path: Path,
        db_type: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Dict[str, DatabaseEntry]:
        """
        Update database from source directory.
        progress_callback: A function (current_count, total_count, status_message) for UI updates.
        """
        if not source_dir.exists():
            self.logger.warning(f"Source directory does not exist: {source_dir}")
            if progress_callback:  # Update progress to indicate no source
                progress_callback(0, 0, f"Source directory for {db_type} missing.")
            return {}

        raw_db = self._load_existing_db(db_path)
        db = {}
        updated_content_or_new_entry = (
            False  # Tracks if SHA/fingerprint changed or new entry
        )
        forced_save_due_to_schema_consistency = (
            False  # Tracks if we need to save due to schema consistency issues
        )

        # Get all files in the source directory, as .txt extension is stripped by updater.
        # Ensure we only process actual files, not subdirectories or hidden files.
        all_license_candidates = []
        if source_dir.exists():
            for item in sorted(source_dir.iterdir()):  # Sort for consistent order
                if item.is_file() and not item.name.startswith("."):
                    all_license_candidates.append(item)

        license_files = all_license_candidates  # Use this list for iteration
        total_files = len(license_files)
        processed_count = 0

        for file_path in license_files:
            # Use .name directly for the license ID, as .txt is already stripped by updater
            name = file_path.name
            current_sha = self._sha256sum(file_path)

            if progress_callback:
                # Pass plain text status message; Rich styling will be handled by CLI.
                progress_callback(
                    processed_count,
                    total_files,
                    f"Processing {db_type}: {name}",
                )

            # Check if file needs updating
            # Raw DB keys are now also .stem based
            if name in raw_db and raw_db[name].get("sha256") == current_sha:
                # File unchanged in content (sha matches)
                entry_data = raw_db[name]
                # Check if the entry in the existing DB is missing the 'embedding' field
                if "embedding" not in entry_data or entry_data.get("embedding") is None:
                    forced_save_due_to_schema_consistency = (
                        True  # This indicates a schema consistency need
                    )

                db[name] = DatabaseEntry(
                    name=name,
                    sha256=entry_data["sha256"],
                    fingerprint=entry_data["fingerprint"],
                    embedding=entry_data.get("embedding"),
                    updated=entry_data["updated"],
                    file_path=file_path,
                )
            else:
                # File is new or changed
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()

                    fingerprint = self._canonical_fingerprint(text)

                    db[name] = DatabaseEntry(
                        name=name,
                        sha256=current_sha,
                        fingerprint=fingerprint,
                        embedding=None,  # Will be computed on demand
                        file_path=file_path,
                    )

                    # Update raw database
                    raw_db[name] = {  # Key is now .stem
                        "sha256": current_sha,
                        "fingerprint": fingerprint,
                        "embedding": None,  # Placeholder, computed on demand
                        "updated": datetime.now(UTC).isoformat(),
                    }

                    updated_content_or_new_entry = True
                    self.logger.info(f"Updated {db_type}: {name}")

                except IOError as e:
                    self.logger.error(f"Failed to read {file_path}: {e}")
                    # Skip this file but continue processing others
            processed_count += 1

        # After processing all files, decide if we need to save the database.
        # We need to save if:
        # 1. Any file's content changed or new files were added (updated_content_or_new_entry).
        # 2. Or, if the existing database (raw_db) was missing expected fields (like 'embedding')
        #    for any entry that has not otherwise changed, to bring its schema up-to-date.

        # We need to build the 'raw_db_to_save' from 'db' because 'db' contains the DatabaseEntry objects
        # with the correct structure and 'None' for embeddings if they are yet to be computed.
        raw_db_to_save = {
            entry.name: {
                "sha256": entry.sha256,
                "fingerprint": entry.fingerprint,
                "embedding": entry.embedding,  # This will be None for uncomputed embeddings
                "updated": entry.updated,
            }
            for entry in db.values()
        }

        if (
            updated_content_or_new_entry
            or forced_save_due_to_schema_consistency
            or not db_path.exists()
        ):
            self._save_db(raw_db_to_save, db_path)  # Save the state derived from 'db'
            self.logger.info(f"Updated/refreshed {db_type} database: {db_path}")
        else:
            self.logger.info(
                f"Database ({db_type}) is up-to-date with source files and schema."
            )

        if progress_callback:
            progress_callback(
                total_files, total_files, f"Finished {db_type} database update."
            )

        return db

    def _get_embedding(self, entry: DatabaseEntry) -> np.ndarray:
        """Get embedding for a database entry, computing if necessary."""
        if entry.embedding is not None:
            return np.array(entry.embedding, dtype=np.float32)

        # Need to compute embedding
        if entry.file_path and entry.file_path.exists():
            try:
                with open(entry.file_path, "r", encoding="utf-8") as f:
                    text = f.read()

                embedding = self.embedding_model.encode(text)
                entry.embedding = embedding.tolist()

                # Update the database file
                self._update_embedding_in_db(entry)

                return embedding
            except IOError as e:
                self.logger.error(
                    f"Failed to read file for embedding: {entry.file_path}: {e}"
                )
                raise
        else:
            raise ValueError(
                f"Cannot compute embedding for {entry.name}: file not found"
            )

    def _update_embedding_in_db(self, entry: DatabaseEntry) -> None:
        """Update embedding in the database file."""
        db_path = self.licenses_db_path

        try:
            raw_db = self._load_existing_db(db_path)
            if entry.name in raw_db:  # entry.name is now .stem
                raw_db[entry.name]["embedding"] = entry.embedding
                raw_db[entry.name]["updated"] = datetime.now(UTC).isoformat()
                self._save_db(raw_db, db_path)
        except Exception as e:
            self.logger.warning(f"Failed to update embedding in database: {e}")

    @property
    def licenses_db(self) -> Dict[str, DatabaseEntry]:
        """Get licenses database, updating if necessary."""
        # This property is now effectively bypassed during initial LicenseAnalyzer.__init__
        # but kept for potential direct usage if needed elsewhere.
        if self._licenses_db is None:
            self.logger.warning(
                "LicenseDatabase.licenses_db accessed before explicit initialization in Analyzer."
            )
            # When this is called, no progress callback is available for direct property access.
            self._licenses_db = self._update_database(
                self.spdx_dir, self.licenses_db_path, "licenses"
            )
        return self._licenses_db

    def get_all_entries(self) -> Dict[str, DatabaseEntry]:  # Return type changed
        """Get all database entries."""
        return self.licenses_db


class LicenseAnalyzer:
    """Main license analyzer class."""

    def __init__(
        self,
        spdx_dir: Optional[Union[str, Path]] = None,
        cache_dir: Optional[Union[str, Path]] = None,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        db_progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ):
        """
        Initialize the license analyzer.

        Args:
            spdx_dir: Path to SPDX licenses directory. If None, it defaults to
                      the app's cache directory (e.g., ~/.cache/license-analyzer/spdx).
            cache_dir: Path to cache directory for analyzer database (default: ~/.cache/license-analyzer/db_cache).
            embedding_model_name: Name of the sentence transformer model
            db_progress_callback: A function (current_count, total_count, status_message) for UI updates during DB update.
        """
        if cache_dir is None:
            # Main cache directory for the application
            cache_dir = (
                Path(user_cache_dir(appname="license-analyzer", appauthor="envolution"))
                / "db_cache"
            )
        else:
            cache_dir = Path(cache_dir)

        if spdx_dir is None:
            # Default SPDX data directory is now within the main cache dir
            spdx_dir = (
                Path(user_cache_dir(appname="license-analyzer", appauthor="envolution"))
                / "spdx"
            )
        else:
            spdx_dir = Path(spdx_dir)

        self.db = LicenseDatabase(spdx_dir, cache_dir, embedding_model_name)
        self.logger = logging.getLogger(__name__)

        # Manually trigger database update with progress callback
        # This bypasses the lazy loading of @property and allows progress reporting
        self.logger.info("Initializing licenses database...")
        self.db._licenses_db = self.db._update_database(
            self.db.spdx_dir, self.db.licenses_db_path, "licenses", db_progress_callback
        )

    def analyze_file(
        self,
        file_path: Union[str, Path],
        top_n: int = 5,
        per_entry_embed_callback: Optional[
            Callable[[str], None]
        ] = None,  # New: for embedding progress
    ) -> List[LicenseMatch]:
        """
        Analyze a single license file.

        Args:
            file_path: Path to the license file to analyze
            top_n: Number of top matches to return
            per_entry_embed_callback: Callback for reporting progress during embedding computation.

        Returns:
            List of LicenseMatch objects sorted by score (descending)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"License file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except IOError as e:
            raise IOError(f"Failed to read license file {file_path}: {e}")

        return self.analyze_text(text, top_n, per_entry_embed_callback)

    def analyze_text(
        self,
        text: str,
        top_n: int = 5,
        per_entry_embed_callback: Optional[
            Callable[[str], None]
        ] = None,  # New: for embedding progress
    ) -> List[LicenseMatch]:
        """
        Analyze license text.

        Args:
            text: License text to analyze
            top_n: Number of top matches to return
            per_entry_embed_callback: Callback for reporting progress during embedding computation.

        Returns:
            List of LicenseMatch objects sorted by score (descending)
        """
        if not text.strip():
            return []

        text_sha = self.db._sha256sum_text(text)
        text_fingerprint = self.db._canonical_fingerprint(text)

        all_entries = self.db.get_all_entries()

        sha_matches = []
        fingerprint_matches = []
        embedding_matches = []

        # Check for exact matches first
        for name, entry in all_entries.items():
            if text_sha == entry.sha256:
                sha_matches.append(
                    LicenseMatch(
                        name=name,
                        score=1.0,
                        method=MatchMethod.SHA256,
                    )
                )
            elif text_fingerprint == entry.fingerprint:
                fingerprint_matches.append(
                    LicenseMatch(
                        name=name,
                        score=1.0,
                        method=MatchMethod.FINGERPRINT,
                    )
                )

        # If we have perfect matches, return them but also check for other perfect matches
        if sha_matches or fingerprint_matches:
            perfect_matches = sha_matches + fingerprint_matches
            # Deduplicate perfect matches if a license matched by both SHA and fingerprint
            seen_names: Set[str] = set()
            deduplicated_perfect_matches = []
            for m in perfect_matches:
                if m.name not in seen_names:
                    deduplicated_perfect_matches.append(m)
                    seen_names.add(m.name)
            # Sort unique perfect matches by method preference (SHA > Fingerprint)
            deduplicated_perfect_matches.sort(
                key=lambda x: x.method == MatchMethod.SHA256, reverse=True
            )

            if len(deduplicated_perfect_matches) >= top_n:
                return deduplicated_perfect_matches[:top_n]
            # Continue to find more matches up to top_n
            remaining = top_n - len(deduplicated_perfect_matches)
        else:
            deduplicated_perfect_matches = []
            remaining = top_n

        # Only compute embeddings if we need more matches
        if remaining > 0:
            try:
                from sentence_transformers import util

                # Note: The first time embedding_model is accessed, it might download the model.
                # This download progress is handled by sentence-transformers' internal logging,
                # which RichHandler will display if verbose logging is enabled.
                text_embedding = self.db.embedding_model.encode(text)

                for name, entry in all_entries.items():
                    if any(
                        match.name == name for match in deduplicated_perfect_matches
                    ):
                        continue

                    try:
                        # Report progress for per-entry embedding computation/retrieval
                        if per_entry_embed_callback:
                            per_entry_embed_callback(
                                f"Computing embedding for {entry.name}..."
                            )

                        entry_embedding = self.db._get_embedding(entry)
                        similarity_raw = float(
                            util.cos_sim(text_embedding, entry_embedding)[0][0]
                        )
                        similarity = max(0.0, float(similarity_raw))

                        embedding_matches.append(
                            LicenseMatch(
                                name=name,
                                score=similarity,
                                method=MatchMethod.EMBEDDING,
                            )
                        )
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to compute embedding similarity for {name}: {e}"
                        )
                        continue

                # Sort embedding matches by score
                embedding_matches.sort(key=lambda x: x.score, reverse=True)

            except ImportError:
                self.logger.warning(
                    "sentence-transformers not available, skipping embedding analysis"
                )

        # Combine all matches
        all_matches = deduplicated_perfect_matches

        # Add embedding matches, avoiding duplicates already present in perfect_matches
        seen_names: Set[str] = set(
            m.name for m in all_matches
        )  # Re-init seen_names for clarity
        for m in embedding_matches:
            if m.name not in seen_names:
                all_matches.append(m)
                seen_names.add(m.name)

        # Sort by score (perfect matches first, then by similarity)
        # Prioritize SHA256 > FINGERPRINT > EMBEDDING for ties, and then by score
        all_matches.sort(
            key=lambda x: (
                x.score,
                x.method == MatchMethod.SHA256,
                x.method == MatchMethod.FINGERPRINT,
            ),
            reverse=True,
        )

        return all_matches[:top_n]

    def analyze_multiple_files(
        self,
        file_paths: List[Union[str, Path]],
        top_n: int = 5,
        analysis_progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Dict[str, List[LicenseMatch]]:
        """
        Analyze multiple license files.

        Args:
            file_paths: List of paths to license files
            top_n: Number of top matches to return per file
            analysis_progress_callback: A function (current_count, total_count, status_message) for UI updates.

        Returns:
            Dictionary mapping file paths to lists of LicenseMatch objects
        """
        results = {}
        total_files = len(file_paths)
        processed_count = 0

        for file_path in file_paths:
            file_path = Path(file_path)
            processed_count += 1

            # Define a nested callback for per-entry embedding computation within this file's analysis
            def per_entry_embed_callback(status_msg: str):
                if analysis_progress_callback:
                    # Prepend the current file's name to the embedding status message
                    analysis_progress_callback(
                        processed_count, total_files, f"[{file_path.name}] {status_msg}"
                    )

            try:
                # First, report that we're analyzing this file
                if analysis_progress_callback:
                    analysis_progress_callback(
                        processed_count, total_files, f"Analyzing {file_path.name}"
                    )

                # Pass the per_entry_embed_callback to analyze_file, which passes it to analyze_text
                matches = self.analyze_file(
                    file_path, top_n, per_entry_embed_callback=per_entry_embed_callback
                )
                results[str(file_path)] = matches
            except Exception as e:
                self.logger.error(f"Failed to analyze {file_path}: {e}")
                results[str(file_path)] = []

        if analysis_progress_callback:
            analysis_progress_callback(
                total_files, total_files, "Finished analyzing files."
            )

        return results

    def get_database_stats(self) -> Dict[str, int]:
        """Get statistics about the license database."""
        return {"total_licenses": len(self.db.licenses_db)}


# Convenience functions for backward compatibility
def analyze_license_file(
    file_path: Union[str, Path],
    top_n: int = 5,
    spdx_dir: Optional[Union[str, Path]] = None,
) -> List[LicenseMatch]:
    """
    Convenience function to analyze a single license file.

    Args:
        file_path: Path to the license file
        top_n: Number of top matches to return
        spdx_dir: Path to SPDX licenses directory

    Returns:
        List of LicenseMatch objects
    """
    # Note: Convenience functions do not expose progress callbacks directly
    analyzer = LicenseAnalyzer(spdx_dir=spdx_dir)
    return analyzer.analyze_file(file_path, top_n)


def analyze_license_text(
    text: str, top_n: int = 5, spdx_dir: Optional[Union[str, Path]] = None
) -> List[LicenseMatch]:
    """
    Convenience function to analyze license text.

    Args:
        text: License text to analyze
        top_n: Number of top matches to return
        spdx_dir: Path to SPDX licenses directory

    Returns:
        List of LicenseMatch objects
    """
    # Note: Convenience functions do not expose progress callbacks directly
    analyzer = LicenseAnalyzer(spdx_dir=spdx_dir)
    return analyzer.analyze_text(text, top_n)
