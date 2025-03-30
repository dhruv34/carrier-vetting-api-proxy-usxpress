# Carrier Vetting API Proxy Setup Guide (GitHub + Railway)

This guide will help you set up the Carrier Vetting API Proxy using GitHub and Railway for deployment.

## 1. GitHub Setup

1. Create a new GitHub repository
2. Extract the provided ZIP file containing the Carrier Vetting API Proxy
3. Initialize the repository and push the code to GitHub:
```bash
cd carrier-vetting-api-proxy
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/your-repo-name.git
git push -u origin main
```

## 2. Local Development Setup

Ensure you have Python 3.11.8 installed (as specified in runtime.txt), then:

### Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

## 3. Configure Environment Variables

Create a `.env` file in the project root for local development:

```bash
HIGHWAY_API_TOKEN=your_highway_api_token
PROXY_API_KEY=your_proxy_api_key
USE_STAGING=true # or false (optional, defaults to false)
```

To generate a new PROXY_API_KEY, run:
```bash
openssl rand -hex 32
```
Save this key to share with HappyRobot later.

## 4. Configure Validation Rules

1. Open `config/conditions.json`
2. Edit the conditions according to your needs:
   - `"active": 1` to enforce a condition
   - `"active": 0` to ignore a condition

## 5. Deploy to Railway

1. Create a Railway account at [railway.app](https://railway.app)
2. Create a new project in Railway
3. Choose "Deploy from GitHub repo"
4. Select your repository
5. Add environment variables in Railway's dashboard:
   - `HIGHWAY_API_TOKEN` (your Highway API token)
   - `PROXY_API_KEY` (your generated API key)
   - `USE_STAGING` (true or false)
6. Railway will automatically deploy your application
7. Get your deployment URL from the Railway dashboard

## 6. Share Access with HappyRobot

Provide HappyRobot with:
1. Your Railway deployment URL
2. Your `PROXY_API_KEY`

## Need Help?

Refer to the included README.md for:
- Detailed API documentation
- Example requests and responses
- Condition configuration details



