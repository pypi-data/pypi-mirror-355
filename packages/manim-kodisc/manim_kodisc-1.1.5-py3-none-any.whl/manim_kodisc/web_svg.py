import tempfile
import os
import random

import requests
from manim import SVGMobject


class WebSVG(SVGMobject):
    def __init__(self, url: str, **kwargs):
        self.url = url
        self.temp_file_path = None
        
        # Download and save SVG content
        svg_path = self._download_svg()
        
        # Initialize the parent SVGMobject with the downloaded file
        super().__init__(file_name=svg_path, **kwargs)
    
    def _download_svg(self) -> str:
        try:
            # Download the SVG content
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
            
            # Verify content type (optional, as some servers may not set correct MIME type)
            content_type = response.headers.get('content-type', '').lower()
            if content_type and 'svg' not in content_type and 'xml' not in content_type:
                # Check if content starts with SVG tag as fallback
                content_start = response.text.strip()[:100].lower()
                if not (content_start.startswith('<?xml') or content_start.startswith('<svg')):
                    raise ValueError(f"URL does not appear to contain SVG content. Content-Type: {content_type}")
            
            # Create a temporary file for the SVG content with a unique random name
            unique_id = random.randint(100000, 999999)
            temp_fd, temp_path = tempfile.mkstemp(suffix='.svg', prefix=f'web_svg_{unique_id}_')
            self.temp_file_path = temp_path
            
            try:
                # Write SVG content to temporary file
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
                    temp_file.write(response.text)
                
                return temp_path
                
            except Exception as e:
                # Clean up file descriptor if writing fails
                try:
                    os.close(temp_fd)
                except:
                    pass
                raise e
                
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to download SVG from {self.url}: {str(e)}")
        except Exception as e:
            # Clean up temporary file if creation fails
            if self.temp_file_path and os.path.exists(self.temp_file_path):
                try:
                    os.unlink(self.temp_file_path)
                except:
                    pass
            raise e
    
    def __del__(self):
        """Clean up the temporary SVG file when the object is destroyed."""
        if hasattr(self, 'temp_file_path') and self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.unlink(self.temp_file_path)
            except:
                # Ignore errors during cleanup
                pass 