# Setup Guide

This guide will walk you through setting up the Intelligent Chat Interface for HR Candidate Profiling.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10 or higher**
- **Git** (for cloning the repository)
- **A text editor** (VS Code, PyCharm, etc.)

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/intelligent-chat-interface.git
cd intelligent-chat-interface
```

### 2. Create a Virtual Environment

It's recommended to use a virtual environment to avoid conflicts with other Python packages.

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download Required Models

The application uses spaCy for natural language processing. Download the English model:

```bash
python -m spacy download en_core_web_sm
```

### 5. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# Create .env file
touch .env  # On Windows: type nul > .env
```

Add the following content to your `.env` file:

```env
# OpenAI API Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

# SerpAPI Configuration (Optional - for LinkedIn scraping)
SERPAPI_KEY=your_serpapi_key_here

# LinkedIn Configuration (Optional)
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password

# Database Configuration
DATABASE_URL=sqlite:///candidate_database.db
```

### 6. Create Required Directories

```bash
mkdir -p data exports logs
```

### 7. Verify Installation

Run a quick test to ensure everything is installed correctly:

```bash
python -c "import streamlit, openai, pdfplumber, spacy; print('All dependencies installed successfully!')"
```

## Getting API Keys

### OpenAI API Key (Required)

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to the API section
4. Create a new API key
5. Copy the key and add it to your `.env` file

**Note**: You'll need to add a payment method to your OpenAI account to use the API.

### SerpAPI Key (Optional)

1. Go to [SerpAPI](https://serpapi.com/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add it to your `.env` file

### LinkedIn Credentials (Optional)

If you want to use direct LinkedIn scraping (not recommended due to ToS), you can add your LinkedIn credentials to the `.env` file. However, using SerpAPI is more reliable and compliant.

## Running the Application

### 1. Start the Application

```bash
streamlit run app.py
```

### 2. Access the Interface

Open your web browser and navigate to:
```
http://localhost:8501
```

### 3. Configure API Keys

1. In the sidebar, enter your OpenAI API key
2. Optionally configure other API keys
3. The application will use these keys for AI features

## Testing the Setup

### 1. Test Resume Parsing

1. Use the sample resume in `data/sample_resume.txt` as a reference
2. Create a PDF version of the sample resume
3. Upload it through the interface
4. Verify that information is extracted correctly

### 2. Test LinkedIn Integration

1. Enter a LinkedIn profile URL (or use mock data)
2. Click "Extract LinkedIn Data"
3. Verify that profile information is extracted

### 3. Test Form Generation

1. Select a candidate
2. Generate a standard HR form
3. Verify that the form is populated correctly
4. Test PDF/Excel export functionality

## Troubleshooting

### Common Issues

#### Python Version Issues
```
Error: Python 3.10+ required
```
**Solution**: Upgrade to Python 3.10 or higher. Check your version with `python --version`.

#### Missing Dependencies
```
Error: ModuleNotFoundError: No module named 'streamlit'
```
**Solution**: Ensure you're in the virtual environment and run `pip install -r requirements.txt`.

#### spaCy Model Issues
```
Error: Can't find model 'en_core_web_sm'
```
**Solution**: Run `python -m spacy download en_core_web_sm`.

#### API Key Issues
```
Error: OpenAI API key not found
```
**Solution**: Ensure your `.env` file is in the root directory and contains the correct API key.

#### Permission Issues
```
Error: Permission denied when creating directories
```
**Solution**: Ensure you have write permissions in the project directory.

### Performance Issues

#### Slow PDF Processing
- Use smaller PDF files
- Ensure PDFs contain selectable text (not scanned images)
- Consider using more powerful hardware

#### API Rate Limits
- Monitor your OpenAI API usage
- Implement request throttling if needed
- Consider upgrading your API plan

## Production Deployment

### Using Docker (Recommended)

1. Create a `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

2. Build and run:
```bash
docker build -t intelligent-chat-interface .
docker run -p 8501:8501 -e OPENAI_API_KEY=your_key intelligent-chat-interface
```

### Using Cloud Platforms

#### Heroku
1. Create a `Procfile`:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

2. Deploy using Heroku CLI or GitHub integration

#### AWS/GCP/Azure
1. Use container services (ECS, Cloud Run, Container Instances)
2. Set up proper environment variable management
3. Configure load balancing and auto-scaling

## Security Considerations

### Environment Variables
- Never commit `.env` files to version control
- Use secure methods to store API keys in production
- Rotate API keys regularly

### Database Security
- Use encrypted databases for production
- Implement proper access controls
- Regular backups and monitoring

### API Security
- Monitor API usage and costs
- Implement rate limiting
- Use API keys with minimal required permissions

## Next Steps

Once you have the application running:

1. **Explore the Features**: Try uploading resumes and generating forms
2. **Customize Forms**: Modify the form templates in `data/sample_hr_form.json`
3. **Add More Data**: Import additional candidate data
4. **Integrate APIs**: Set up additional API integrations
5. **Deploy**: Deploy to a production environment

## Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs in the `logs/` directory
3. Create an issue on GitHub
4. Check the main README.md for additional information

---

**Happy profiling! 🚀**
