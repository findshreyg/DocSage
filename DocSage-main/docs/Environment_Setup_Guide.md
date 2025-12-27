# 🚀 DocSage Setup Guide

> Get DocSage running in 15 minutes or less!

This guide will help you set up DocSage quickly and easily. We'll walk you through everything step by step.

## ✅ What You'll Need

### Accounts (Free to start)
- **AWS Account** - For secure cloud storage ([Sign up here](https://aws.amazon.com/free/))
- **Mistral AI Account** - For AI document analysis ([Sign up here](https://console.mistral.ai/))

### Software
- **Docker Desktop** - Easiest way to run DocSage ([Download here](https://www.docker.com/products/docker-desktop/))
- **Git** - To download DocSage ([Download here](https://git-scm.com/downloads))

### Time Required
- **Setup**: ~15 minutes
- **Testing**: ~5 minutes

## 🎯 Quick Setup (Recommended)

### Step 1: Download DocSage
```bash
git clone <repository-url>
cd DocSage
```

### Step 2: Get Your API Keys

#### AWS Setup (5 minutes)
1. **Go to AWS Console** → Sign in to your AWS account
2. **Create S3 Bucket**:
   - Go to S3 → Create bucket
   - Name: `your-docsage-bucket` (must be globally unique)
   - Region: `us-east-1` (recommended)
   - Keep default settings → Create bucket

3. **Create Cognito User Pool**:
   - Go to Cognito → Create User Pool
   - Name: `DocSage-Users`
   - Keep default settings → Create pool
   - **Save the User Pool ID**

4. **Create App Client**:
   - In your User Pool → App integration → Create app client
   - Name: `DocSage-Client`
   - Generate client secret: ✅ Yes
   - **Save the Client ID and Client Secret**

5. **Get AWS Credentials**:
   - Go to IAM → Users → Create user
   - Attach policies: `AmazonS3FullAccess`, `AmazonCognitoPowerUser`, `AmazonDynamoDBFullAccess`
   - Create access key → **Save Access Key ID and Secret**

#### Mistral AI Setup (2 minutes)
1. **Go to [Mistral Console](https://console.mistral.ai/)**
2. **Sign up/Login** → Go to API Keys
3. **Create new API key** → **Save the API key**

### Step 3: Configure DocSage
```bash
# Copy the example configuration
cp .env.example .env

# Edit with your credentials (use any text editor)
nano .env
```

**Fill in your `.env` file**:
```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-docsage-bucket

# AWS Cognito
COGNITO_USER_POOL_ID=your_user_pool_id_here
COGNITO_APP_CLIENT_ID=your_client_id_here
COGNITO_CLIENT_SECRET=your_client_secret_here

# DynamoDB Tables (these will be created automatically)
DDB_TABLE=IDPMetadata
DYNAMODB_CONVERSATION_TABLE=IDPConversation

# Mistral AI
MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_API_URL=https://api.mistral.ai/v1/chat/completions
MISTRAL_LLM_MODEL=mistral-large-latest
```

### Step 4: Start DocSage
```bash
# Start all services with Docker
docker-compose up -d

# Wait a moment for services to start, then test
curl http://localhost:8001/auth/health
curl http://localhost:8002/file/health
curl http://localhost:8003/conversation/health
curl http://localhost:8004/llm/health
```

**You should see**: `{"health": "All Good"}` for each service.

### Step 5: Test Your Setup
```bash
# Test each service health endpoint
curl http://localhost:8001/auth/health
curl http://localhost:8002/file/health
curl http://localhost:8003/conversation/health
curl http://localhost:8004/llm/health

# If everything works, you'll see:
# {"health": "All Good"} for each service
```

## 🎉 You're Done!

DocSage is now running! Here's what you can do:

- **API Documentation**: Visit `http://localhost:8001/docs` (and 8002, 8003, 8004)
- **Test with Postman**: Import `DocSage_Complete_Testing_Collection.json`
- **Follow the API Guide**: Check `docs/API_Guide.md` for examples

## 🔧 Alternative Setup (Without Docker)

If you prefer not to use Docker:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start each service in separate terminals
cd auth_services && uvicorn main:app --port 8001 &
cd file_services && uvicorn main:app --port 8002 &
cd conversation_services && uvicorn main:app --port 8003 &
cd llm_services && uvicorn main:app --port 8004 &
```

## 💰 Cost Estimates

### AWS Costs (Pay-as-you-use)
- **S3 Storage**: ~$0.023/GB/month
- **DynamoDB**: Free tier covers most usage
- **Cognito**: Free for up to 50,000 users

### Mistral AI Costs
- **mistral-large-latest**: ~$0.008/1K tokens
- **Typical document analysis**: $0.01-0.05 per document

**Example**: Processing 100 documents/month ≈ $5-10 total cost

## 🚨 Troubleshooting

### "Services won't start"
```bash
# Check if ports are in use
lsof -i :8001 -i :8002 -i :8003 -i :8004

# Check Docker
docker-compose ps
docker-compose logs
```

### "Authentication errors"
- Double-check your AWS Cognito credentials in `.env`
- Verify your User Pool allows password authentication
- Make sure your AWS region is correct

### "File upload fails"
- Check your S3 bucket name and region
- Verify AWS credentials have S3 permissions
- Ensure bucket exists and is accessible

### "AI not responding"
- Verify Mistral AI API key is valid
- Check your Mistral account has credits
- Test API key: `curl -H "Authorization: Bearer YOUR_KEY" https://api.mistral.ai/v1/models`

### "DynamoDB errors"
The tables are created automatically when you first use the system. If you see errors:
```bash
# Check if tables exist
aws dynamodb list-tables --region us-east-1

# If missing, they'll be created on first use
```

## ✅ Verification Checklist

After setup, make sure:
- [ ] All 4 services respond to health checks
- [ ] You can create a user account
- [ ] You can upload a document
- [ ] You can ask questions about the document
- [ ] Conversations are saved properly

## 🔒 Security Notes

- **Never commit your `.env` file** - it contains sensitive credentials
- **Use strong passwords** for your test accounts
- **Rotate your API keys** periodically
- **Monitor your AWS costs** in the AWS Console

## 📞 Need Help?

1. **Check the logs**: `docker-compose logs [service-name]`
2. **Test individual services**: Use the health check URLs
3. **Review your `.env` file**: Make sure all values are correct
4. **Check AWS Console**: Verify your resources exist

## 🎯 Next Steps

Once DocSage is running:

1. **Read the API Guide**: `docs/API_Guide.md`
2. **Try the Postman Collection**: Import `DocSage_Complete_Testing_Collection.json`
3. **Upload your first document** and start asking questions!
4. **Explore the interactive docs**: Visit `http://localhost:8001/docs`

## 📚 Useful Links

- [AWS Free Tier](https://aws.amazon.com/free/) - Start with free AWS resources
- [Mistral AI Pricing](https://mistral.ai/technology/#pricing) - Understand AI costs
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) - Container platform
- [Postman](https://www.postman.com/) - API testing tool

---

**🎉 Congratulations!** You now have DocSage running and ready to process your documents intelligently!