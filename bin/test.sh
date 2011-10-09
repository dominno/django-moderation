#!/bin/bash

echo "-------------------------------"
echo "Running tests for django 1.1.X"
echo "-------------------------------"
echo ""

bin/test-1.1

echo "-------------------------------"
echo "Running tests for django 1.2.X"
echo "-------------------------------"
echo ""

bin/test-1.2

echo "-------------------------------"
echo "Running tests for django 1.3"
echo "-------------------------------"
echo ""

bin/test-1.3