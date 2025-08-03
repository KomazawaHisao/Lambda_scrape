#!/bin/bash
set -e

echo "💡 Creating deployment package..."
if [ ! -d package ]; then
  mkdir package
  pip install requests beautifulsoup4 dotenv -t ./package
fi
cp lambda_function.py package/
cd package
zip -r ../function.zip .
cd ..

echo "💡 Deploying to AWS Lambda..."
aws lambda update-function-code \
  --function-name MakeVector \
  --zip-file fileb://function.zip

echo " complete!"
