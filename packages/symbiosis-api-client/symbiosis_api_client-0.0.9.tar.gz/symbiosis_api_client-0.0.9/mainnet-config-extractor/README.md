# Mainnet Config JSON Extractor

This tool extracts the TypeScript configuration from `mainnet.ts` and converts it to a plain JSON file.

## Instructions

### 1. Clone the repository and navigate to this folder

```bash
git clone https://github.com/symbiosis-finance/js-sdk.git
cd js-sdk/mainnet-config-extractor
```

### 2. Install dependencies

```bash
npm install
```

### 3. Run the extraction script

```bash
npm run extract
```

This will create a `mainnet-config.json` file in the current directory.

## How it works

The extraction script:
1. Reads the `src/crosschain/config/mainnet.ts` file
2. Includes minimal type definitions for ChainId enum and Token class
3. Evaluates the config object
4. Serializes it to handle Token instances and other special types
5. Outputs the result as a JSON file

## Files included

- `package.json` - Minimal package configuration with required dependencies
- `extract-config.ts` - The extraction script
- `src/crosschain/config/mainnet.ts` - The source TypeScript config file (copied from main repo)
- `README.md` - This file

## Output

The script will generate `mainnet-config.json` containing the entire configuration in JSON format, with:
- All ChainId enum values resolved to their numeric values
- All Token instances converted to plain objects
- Proper handling of all nested structures

## Notes

- The script uses `ts-node` with `--transpile-only` flag to skip type checking for faster execution
- All necessary type definitions are included inline in the extraction script
- No need to copy the entire SDK structure - only the mainnet.ts file is required
