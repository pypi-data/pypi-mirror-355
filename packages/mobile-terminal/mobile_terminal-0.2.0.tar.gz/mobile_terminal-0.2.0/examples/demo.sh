#!/bin/bash
# Demo script that asks for user input periodically

echo "Starting deployment simulation..."
sleep 2

echo "Checking prerequisites..."
sleep 1

echo "Building application..."
for i in {1..5}; do
    echo "  Compiling module $i/5..."
    sleep 1
done

echo ""
read -p "Run tests before deployment? [Y/n] " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    echo "Running tests..."
    sleep 2
    echo "✓ All tests passed!"
fi

echo ""
echo "Ready to deploy to production."
read -p "Are you sure you want to continue? [y/N] " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Deploying to production..."
    for i in {1..10}; do
        echo "  Progress: $((i*10))%"
        sleep 1
    done
    echo "✓ Deployment complete!"
else
    echo "Deployment cancelled."
fi