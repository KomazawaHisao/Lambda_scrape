#!/bin/bash
set -e

echo "💡 Creating deployment package..."
mkdir -p package
pip install requests beautifulsoup4 -t ./package
cp lambda_function.py package/
cd package
zip -r ../function.zip .
cd ..

echo " complete!"
