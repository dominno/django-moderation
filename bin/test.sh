#!/bin/bash

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

echo "-------------------------------"
echo "Running tests for django 1.4"
echo "-------------------------------"
echo ""

bin/test-1.4
