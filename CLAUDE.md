# BOTC-Bot Development Guidelines

## Commands
- Run a single test: `python -m unittest time_utils.test_time_utils.TestTimeUtils.test_specific_method`
- Run all tests: `python -m unittest discover`
- Run the bot: `python bot.py`
- Build Docker image: `docker build -t botc .`
- Run in Docker: `docker run -v $(pwd):/app -v $(pwd)/bot_configs/${BOT_NAME}.py:/app/config.py -d --name ${BOT_NAME} botc`

## Code Style
- **Indentation**: 4 spaces
- **Line length**: ~120 characters
- **Naming**: snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants
- **Privacy**: prefix private methods/variables with underscore (_)
- **Type annotations**: Use them for all function parameters and return values
- **Imports**: Group by standard library, third-party, then local imports
- **Docstrings**: Triple double-quotes with parameter descriptions
- **Error handling**: Use specific exceptions, log before handling or re-raising
- **Testing**: Use unittest framework, class methods prefixed with test_

## Project Organization
- Bot configs in bot_configs/ directory
- Model classes in model/ directory
- Utility modules in separate directories (e.g., time_utils/)