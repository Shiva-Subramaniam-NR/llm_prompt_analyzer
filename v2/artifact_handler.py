"""
Artifact Handler for File Upload Support

Handles extraction and validation of artifacts (PDFs, images, text files)
mentioned in prompts.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ArtifactType(Enum):
    """Supported artifact types"""
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    UNKNOWN = "unknown"


@dataclass
class Artifact:
    """Represents an uploaded artifact"""
    file_path: str
    artifact_type: ArtifactType
    exists: bool
    file_size: int  # in bytes
    extracted_text: Optional[str] = None
    error_message: Optional[str] = None


class ArtifactHandler:
    """
    Handles artifact file operations and extraction.

    Phase 1: Basic validation and text extraction without LLM
    """

    SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    SUPPORTED_TEXT_EXTENSIONS = {'.txt', '.md', '.json', '.csv'}
    SUPPORTED_PDF_EXTENSIONS = {'.pdf'}

    def __init__(self):
        """Initialize artifact handler"""
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required libraries are available"""
        self.has_pdfplumber = False
        self.has_pillow = False

        try:
            import pdfplumber
            self.has_pdfplumber = True
        except ImportError:
            pass

        try:
            from PIL import Image
            self.has_pillow = True
        except ImportError:
            pass

    def process_artifacts(
        self,
        artifacts: Dict[str, str]
    ) -> Tuple[Dict[str, Artifact], List[str]]:
        """
        Process multiple artifacts and return validated results.

        Args:
            artifacts: Dict mapping artifact names to file paths
                      e.g., {'document': 'path/to/doc.pdf', 'image': 'path/to/img.jpg'}

        Returns:
            Tuple of (processed_artifacts_dict, validation_issues_list)
        """
        processed = {}
        issues = []

        for name, file_path in artifacts.items():
            artifact = self.process_single_artifact(name, file_path)
            processed[name] = artifact

            if not artifact.exists:
                issues.append(f"Artifact '{name}' not found at path: {file_path}")
            elif artifact.error_message:
                issues.append(f"Error processing '{name}': {artifact.error_message}")

        return processed, issues

    def process_single_artifact(self, name: str, file_path: str) -> Artifact:
        """
        Process a single artifact file.

        Args:
            name: Logical name of the artifact (e.g., 'research_document')
            file_path: Path to the file

        Returns:
            Artifact object with processing results
        """
        # Check if file exists
        path = Path(file_path)
        if not path.exists():
            return Artifact(
                file_path=file_path,
                artifact_type=ArtifactType.UNKNOWN,
                exists=False,
                file_size=0,
                error_message="File not found"
            )

        # Determine artifact type
        artifact_type = self._detect_artifact_type(path)
        file_size = path.stat().st_size

        # Extract text based on type
        extracted_text = None
        error_message = None

        try:
            if artifact_type == ArtifactType.PDF:
                extracted_text = self._extract_pdf_text(path)
            elif artifact_type == ArtifactType.TEXT:
                extracted_text = self._extract_text_file(path)
            elif artifact_type == ArtifactType.IMAGE:
                extracted_text = self._get_image_metadata(path)
        except Exception as e:
            error_message = str(e)

        return Artifact(
            file_path=file_path,
            artifact_type=artifact_type,
            exists=True,
            file_size=file_size,
            extracted_text=extracted_text,
            error_message=error_message
        )

    def _detect_artifact_type(self, path: Path) -> ArtifactType:
        """Detect artifact type from file extension"""
        extension = path.suffix.lower()

        if extension in self.SUPPORTED_PDF_EXTENSIONS:
            return ArtifactType.PDF
        elif extension in self.SUPPORTED_IMAGE_EXTENSIONS:
            return ArtifactType.IMAGE
        elif extension in self.SUPPORTED_TEXT_EXTENSIONS:
            return ArtifactType.TEXT
        else:
            return ArtifactType.UNKNOWN

    def _extract_pdf_text(self, path: Path) -> str:
        """Extract text from PDF file"""
        if not self.has_pdfplumber:
            return "[PDF text extraction requires 'pdfplumber' library: pip install pdfplumber]"

        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {i+1} ---\n{page_text}")

            if not text_parts:
                return "[No text could be extracted from PDF]"

            full_text = "\n\n".join(text_parts)

            # Truncate if too long (keep first 10000 chars)
            if len(full_text) > 10000:
                full_text = full_text[:10000] + "\n\n[... truncated for length ...]"

            return full_text

        except Exception as e:
            return f"[Error extracting PDF text: {str(e)}]"

    def _extract_text_file(self, path: Path) -> str:
        """Extract text from plain text file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Truncate if too long
            if len(text) > 10000:
                text = text[:10000] + "\n\n[... truncated for length ...]"

            return text

        except Exception as e:
            return f"[Error reading text file: {str(e)}]"

    def _get_image_metadata(self, path: Path) -> str:
        """Get basic metadata from image file"""
        if not self.has_pillow:
            return f"[Image file present: {path.name}. Install 'Pillow' for metadata: pip install Pillow]"

        try:
            from PIL import Image

            with Image.open(path) as img:
                return (
                    f"[Image: {path.name}]\n"
                    f"Format: {img.format}\n"
                    f"Size: {img.size[0]}x{img.size[1]} pixels\n"
                    f"Mode: {img.mode}"
                )

        except Exception as e:
            return f"[Error reading image: {str(e)}]"

    def validate_artifacts_mentioned_in_prompt(
        self,
        prompt: str,
        artifacts: Dict[str, Artifact]
    ) -> List[str]:
        """
        Check if artifacts mentioned in prompt are actually provided.

        Args:
            prompt: The user or system prompt text
            artifacts: Dictionary of processed artifacts

        Returns:
            List of validation issues
        """
        issues = []

        # Common keywords that suggest artifacts
        artifact_keywords = {
            'document': ['document', 'paper', 'report', 'pdf'],
            'image': ['image', 'picture', 'photo', 'screenshot'],
            'file': ['file', 'attachment']
        }

        prompt_lower = prompt.lower()

        # Check for document mentions
        for keyword_type, keywords in artifact_keywords.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    # User mentioned this type of artifact
                    found = False
                    for name, artifact in artifacts.items():
                        if keyword_type == 'document' and artifact.artifact_type == ArtifactType.PDF:
                            found = True
                        elif keyword_type == 'image' and artifact.artifact_type == ArtifactType.IMAGE:
                            found = True
                        elif artifact.artifact_type in [ArtifactType.PDF, ArtifactType.IMAGE, ArtifactType.TEXT]:
                            found = True

                    if not found and not artifacts:
                        issues.append(
                            f"Prompt mentions '{keyword}' but no artifacts were provided"
                        )
                        break  # Only report once per keyword type

        return issues


def get_installation_instructions() -> str:
    """Get instructions for installing optional dependencies"""
    return """
To enable full artifact support, install these optional dependencies:

    pip install pdfplumber     # For PDF text extraction
    pip install Pillow         # For image metadata

Without these, artifacts can still be validated for existence,
but text extraction will be limited.
"""
