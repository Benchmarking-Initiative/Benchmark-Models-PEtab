# Build library as source distribution with included model files

# Either, call `./build.sh` followed by `pip install build/dist/*`
# Or directly install from source via `pip install -e .`

BUILD_DIR="build"
CODE_DIR="benchmark_models_petab"
DATA_DIR="Benchmark-Models"

# Create build folder
if [ -e $BUILD_DIR ]; then
    echo "Remove build folder $BUILD_DIR"
    exit 1
fi
mkdir $BUILD_DIR

# Copy code
cp -r \
  $CODE_DIR \
  "setup.cfg" "setup.py" "pyproject.toml" "MANIFEST.in" \
  "../../LICENSE" "../../README.md" \
  $BUILD_DIR
# Remove link
rm -rf $BUILD_DIR/$CODE_DIR/$DATA_DIR
# Copy data
cp -r "../../$DATA_DIR" $BUILD_DIR/$CODE_DIR

# Hop into
cd $BUILD_DIR

# Build
pip install --upgrade build
python -m build --sdist
