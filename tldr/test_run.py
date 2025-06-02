import logging

from pygments.formatters.markdown import MarkdownFormatter
from pygments.formatters.tldr import TLDRFormatter

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s(): - %(message)s",
    handlers=[logging.StreamHandler()]
)

logging.debug("TLDRFormatter STARTED")

# Example usage and testing
if __name__ == '__main__':
    import sys
    import os
    from pygments import highlight
    from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
    from pygments.util import ClassNotFound

    def main():
        """
        Main function to process a file and output Markdown formatted code.
        Usage: python markdown_formatter.py <filename> [options]
        """
        # if len(sys.argv) < 2:
        #     print("Usage: python markdown_formatter.py <filename> [--style=emphasis|callout|heading] [--linenos] [--full]")
        #     print("Example: python markdown_formatter.py example.py --style=callout --linenos")
        #     return
        #
        # filename = sys.argv[1]
        # filename = "/Users/csimoes/Projects/Python/conductor/app/processor/base_processor.py"
        filename = "/Users/csimoes/IdeaProjects/Amazon/AmazonScraper/adtrimmer-core/src/main/java/org/simoes/app/AutoBidder8.java"

        # Check if file exists
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' not found.")
            return

        # Parse command line options
        show_linenos = False
        full_document = False

        try:
            # Read the file
            with open(filename, 'r', encoding='utf-8') as f:
                code = f.read()

            # Get appropriate lexer for the file
            try:
                lexer = get_lexer_for_filename(filename)
            except ClassNotFound:
                # Fallback to text lexer if file type not recognized
                print(f"Warning: Could not determine lexer for '{filename}', using text")
                lexer = get_lexer_by_name('text')

            # Create formatter with options
            formatter_options = {
                'highlight_functions': True,
                'linenos': show_linenos,
                'full': full_document
            }

            # Auto-detect language from lexer
            if hasattr(lexer, 'aliases') and lexer.aliases:
                formatter_options['lang'] = lexer.aliases[0]

            # Set title for full documents
            if full_document:
                formatter_options['title'] = f'Code Analysis: {os.path.basename(filename)}'

            formatter = TLDRFormatter(**formatter_options)

            # Generate the highlighted code
            result = highlight(code, lexer, formatter)

            # Output the result
            logging.info(f"Result:\n{result}")

        except Exception as e:
            print(f"Error processing file: {e}")
            return

    main()