# Environment Setup Guide

## 🔐 Secure API Key Management

This guide shows you how to securely set up your API keys for the Intelligent Chat Interface.

## 🚀 Quick Setup

### Option 1: Interactive Setup (Recommended)
```bash
python setup_env.py
```
This script will securely prompt you for your API keys and create the `.env` file.

### Option 2: Manual Setup
```bash
cp .env.example .env
# Edit .env file with your API keys
```

## 📋 Required API Keys

### OpenAI API Key (Required)
- **Purpose**: AI-powered form generation and chat features
- **Get it from**: https://platform.openai.com/api-keys
- **Cost**: Pay-per-use (very affordable for testing)
- **Required for**: All AI features, form generation

### SerpAPI Key (Optional)
- **Purpose**: Enhanced LinkedIn profile scraping
- **Get it from**: https://serpapi.com/
- **Cost**: Free tier available, paid plans for higher usage
- **Required for**: Reliable LinkedIn data extraction

### LinkedIn Credentials (Optional)
- **Purpose**: Direct LinkedIn profile access
- **Required for**: Direct LinkedIn integration (not recommended due to ToS)

## 🔒 Security Best Practices

### ✅ Do's
- Use the `.env` file for API keys
- Keep your `.env` file local and never commit it
- Use strong, unique API keys
- Regularly rotate your API keys
- Monitor your API usage and costs

### ❌ Don'ts
- Never commit `.env` files to version control
- Don't share API keys in chat or email
- Don't hardcode API keys in your code
- Don't use production API keys for development

## 📁 File Structure

```
intelligent-chat-interface/
├── .env                    # Your API keys (DO NOT COMMIT)
├── .env.example           # Template for environment variables
├── .gitignore             # Excludes .env from version control
├── setup_env.py           # Interactive setup script
└── config.py              # Loads environment variables
```

## 🔧 Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI features | Yes | `sk-...` |
| `SERPAPI_KEY` | SerpAPI key for LinkedIn scraping | No | `abc123...` |
| `LINKEDIN_EMAIL` | LinkedIn account email | No | `user@example.com` |
| `LINKEDIN_PASSWORD` | LinkedIn account password | No | `password123` |

## 🚨 Troubleshooting

### API Key Not Working
1. Check that your `.env` file exists
2. Verify the API key is correct
3. Ensure no extra spaces or quotes around the key
4. Restart the application after changing keys

### Environment Variables Not Loading
1. Make sure `python-dotenv` is installed: `pip install python-dotenv`
2. Check that `.env` file is in the project root
3. Verify the variable names match exactly

### Application Not Starting
1. Check that all required dependencies are installed
2. Verify your Python version (3.10+)
3. Check the logs for specific error messages

## 💡 Tips

- **Start with OpenAI only**: You can run the app with just the OpenAI API key
- **Test with free tiers**: Most APIs offer free tiers for testing
- **Monitor usage**: Keep track of your API usage to avoid unexpected costs
- **Use placeholders**: The app works with placeholder values for optional keys

## 🆘 Need Help?

- Check the main README.md for detailed setup instructions
- Run `python setup_env.py` for interactive setup
- Check the logs in the `logs/` directory for error details
- Ensure all dependencies are installed: `pip install -r requirements.txt`
