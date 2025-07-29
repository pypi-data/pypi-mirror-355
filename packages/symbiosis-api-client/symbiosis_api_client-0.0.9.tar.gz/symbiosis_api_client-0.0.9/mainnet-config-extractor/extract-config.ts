import * as fs from 'fs';
import * as path from 'path';

// Define minimal ChainId enum with only the values we need
enum ChainId {
    ETH_MAINNET = 1,
    BSC_MAINNET = 56,
    MATIC_MAINNET = 137,
    AVAX_MAINNET = 43114,
    TELOS_MAINNET = 40,
    KAVA_MAINNET = 2222,
    BOBA_MAINNET = 288,
    BOBA_BNB = 56288,
    ZK_SYNC_MAINNET = 324,
    ARBITRUM_MAINNET = 42161,
    OP_MAINNET = 10,
    ARBITRUM_NOVA = 42170,
    POLYGON_ZK = 1101,
    LINEA_MAINNET = 59144,
    MANTLE_MAINNET = 5000,
    BASE_MAINNET = 8453,
    TRON_MAINNET = 728126428,
    SCROLL_MAINNET = 534352,
    MANTA_MAINNET = 169,
    METIS_MAINNET = 1088,
    BAHAMUT_MAINNET = 5165,
    MODE_MAINNET = 34443,
    RSK_MAINNET = 30,
    BLAST_MAINNET = 81457,
    MERLIN_MAINNET = 4200,
    ZKLINK_MAINNET = 810180,
    CORE_MAINNET = 1116,
    TAIKO_MAINNET = 167000,
    SEI_EVM_MAINNET = 1329,
    ZETA_MAINNET = 7000,
    CRONOS_MAINNET = 25,
    FRAXTAL_MAINNET = 252,
    GRAVITY_MAINNET = 1625,
    BSQUARED_MAINNET = 223,
    TON_MAINNET = 85918,
    CRONOS_ZK_MAINNET = 388,
    MORPH_MAINNET = 2818,
    SOLANA_MAINNET = 5426,
    GOAT_MAINNET = 2345,
    SONIC_MAINNET = 146,
    ABSTRACT_MAINNET = 2741,
    GNOSIS_MAINNET = 100,
    BERACHAIN_MAINNET = 80094,
    UNICHAIN_MAINNET = 130,
    SONEIUM_MAINNET = 1868,
    OPBNB_MAINNET = 204,
    HYPERLIQUID_MAINNET = 999,
    BTC_MAINNET = 3652501241,
}

// Define minimal types
type Icons = {
    large?: string
    small?: string
}

type TokenConstructor = {
    name?: string
    symbol?: string
    address: string
    decimals: number
    chainId: ChainId
    isNative?: boolean
    chainFromId?: ChainId
    icons?: Icons
    userToken?: boolean
    deprecated?: boolean
    attributes?: {
        solana?: string
        ton?: string
    }
}

class Token {
    public readonly decimals: number
    public readonly symbol?: string
    public readonly name?: string
    public readonly chainId: ChainId
    public readonly address: string
    public readonly icons?: Icons
    public readonly chainFromId?: ChainId
    public readonly isNative: boolean
    public readonly userToken?: boolean
    public readonly deprecated: boolean
    public readonly attributes?: {
        solana?: string
        ton?: string
    }

    constructor(params: TokenConstructor) {
        this.decimals = params.decimals
        this.symbol = params.symbol
        this.name = params.name
        this.chainId = params.chainId
        this.isNative = !!params.isNative
        this.icons = params.icons
        this.chainFromId = params.chainFromId
        this.userToken = params.userToken
        this.deprecated = !!params.deprecated
        this.attributes = params.attributes
        this.address = params.address
    }

    public get isToken(): boolean {
        return true
    }
}

type ChainConfig = {
    id: ChainId
    rpc: string
    spareRpcs?: string[]
    dexFee: number
    filterBlockOffset: number
    stables: TokenConstructor[]
    metaRouter: string
    metaRouterGateway: string
    multicallRouter: string
    router: string
    bridge: string
    synthesis: string
    portal: string
    fabric: string
    tonPortal?: string
    partnerFeeCollector?: string
}

type AdvisorConfig = {
    url: string
}

type OmniPoolConfig = {
    chainId: ChainId
    address: string
    oracle: string
    generalPurpose: boolean
}

type SwapLimit = {
    chainId: ChainId
    address: string
    min: string
    max: string
}

type BtcConfig = {
    btc: Token
    symBtc: {
        address: string
        chainId: ChainId
    }
    forwarderUrl: string
}

type Config = {
    advisor: AdvisorConfig
    omniPools: OmniPoolConfig[]
    revertableAddress: Partial<Record<ChainId, string>> & { default: string }
    limits: SwapLimit[]
    chains: ChainConfig[]
    refundAddress: string
    btcConfigs: BtcConfig[]
}

// Read and parse the mainnet.ts file
const mainnetPath = path.join(__dirname, 'src/crosschain/config/mainnet.ts');
const mainnetContent = fs.readFileSync(mainnetPath, 'utf8');

// Extract the config object using regex and string manipulation
const configMatch = mainnetContent.match(/export\s+const\s+config:\s*Config\s*=\s*(\{[\s\S]*\})\s*$/);
if (!configMatch) {
    console.error('Could not find config export in mainnet.ts');
    process.exit(1);
}

// Function to serialize config with proper handling
function serializeConfig(obj: any): any {
    if (obj === null || obj === undefined) {
        return obj;
    }

    if (typeof obj === 'bigint') {
        return obj.toString();
    }

    if (obj instanceof Token) {
        return {
            chainId: obj.chainId,
            address: obj.address,
            decimals: obj.decimals,
            symbol: obj.symbol,
            name: obj.name,
            isNative: obj.isNative,
            isToken: obj.isToken,
            icons: obj.icons,
            attributes: obj.attributes,
            deprecated: obj.deprecated
        };
    }

    if (Array.isArray(obj)) {
        return obj.map(item => serializeConfig(item));
    }

    if (typeof obj === 'object') {
        const result: any = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                result[key] = serializeConfig(obj[key]);
            }
        }
        return result;
    }

    return obj;
}

// Create a function wrapper to evaluate the config
const evalWrapper = `
${Token.toString()}

const ChainId = ${JSON.stringify(ChainId)};

const config = ${configMatch[1]};

return config;
`;

try {
    // Evaluate the config
    const configFunc = new Function(evalWrapper);
    const config = configFunc();

    // Serialize the config
    const serializedConfig = serializeConfig(config);

    // Convert to JSON
    const jsonConfig = JSON.stringify(serializedConfig, null, 2);

    // Write to file
    const outputPath = path.join(__dirname, 'mainnet-config.json');
    fs.writeFileSync(outputPath, jsonConfig);

    console.log(`Config successfully written to ${outputPath}`);
    console.log(`File size: ${jsonConfig.length} characters`);
} catch (error) {
    console.error('Error evaluating config:', error);
    process.exit(1);
}
