const GIIKER_SERVICE_UUID              = "0000aadb-0000-1000-8000-00805f9b34fb";
const GIIKER_CHARACTERISTIC_UUID       = "0000aadc-0000-1000-8000-00805f9b34fb";

const GAN_SERVICE_UUID                 = "0000fff0-0000-1000-8000-00805f9b34fb";
const GAN_CHARACTERISTIC_UUID         = "0000fff5-0000-1000-8000-00805f9b34fb";
const GAN_SERVICE_UUID_META            = "0000180a-0000-1000-8000-00805f9b34fb";
const GAN_CHARACTERISTIC_VERSION       = "00002a28-0000-1000-8000-00805f9b34fb";
const GAN_CHARACTERISTIC_UUID_HARDWARE = "00002a23-0000-1000-8000-00805f9b34fb";
const GAN_ENCRYPTION_KEYS = [
    "NoRgnAHANATADDWJYwMxQOxiiEcfYgSK6Hpr4TYCs0IG1OEAbDszALpA",
    "NoNg7ANATFIQnARmogLBRUCs0oAYN8U5J45EQBmFADg0oJAOSlUQF0g",
];

const GOCUBE_SERVICE_UUID              = "6e400001-b5a3-f393-e0a9-e50e24dcca9e";
const GOCUBE_CHARACTERISTIC_UUID       = "6e400003-b5a3-f393-e0a9-e50e24dcca9e";

// Ordered to match 5-bit move index from GAN BLE packets
const GAN_MOVES = [
    "U", "U'", "U2", "D", "D'", "D2",
    "R", "R'", "R2", "L", "L'", "L2",
    "F", "F'", "F2", "B", "B'", "B2",
];

let device           = null;
let ganDecoder       = null;
let ganPrevMoveCount = -1;

async function sendMove(turn) {
    try {
        await fetch("/move?turn=" + encodeURIComponent(turn));
    } catch (ex) {
        console.error("Failed to send move to backend:", ex);
    }
}

async function connect() {
    try {
        device = await navigator.bluetooth.requestDevice({
            filters: [
                { namePrefix: "Gi" },
                { namePrefix: "GAN-" },
                { namePrefix: "GoCube_" },
            ],
            optionalServices: [
                GIIKER_SERVICE_UUID,
                GAN_SERVICE_UUID,
                GAN_SERVICE_UUID_META,
                GOCUBE_SERVICE_UUID,
                "battery_service",
            ],
        });
        const server = await device.gatt.connect();
        const name   = server.device.name;
        if (name.startsWith("GAN-")) {
            await connectGan(server);
        } else if (name.startsWith("Gi")) {
            await connectGiiker(server);
        } else if (name.startsWith("GoCube_")) {
            await connectGoCube(server);
        } else {
            throw new Error("Unknown device: " + name);
        }
    } catch (ex) {
        device = null;
        console.error("Connection error:", ex);
        throw ex;
    }
}

async function connectGan(server) {
    ganDecoder = null;
    const meta      = await server.getPrimaryService(GAN_SERVICE_UUID_META);
    const verChar   = await meta.getCharacteristic(GAN_CHARACTERISTIC_VERSION);
    const verVal    = await verChar.readValue();
    const version   = verVal.getUint8(0) << 16 | verVal.getUint8(1) << 8 | verVal.getUint8(2);

    if (version > 0x010007 && (version & 0xfffe00) === 0x010000) {
        const hwChar = await meta.getCharacteristic(GAN_CHARACTERISTIC_UUID_HARDWARE);
        const hwVal  = await hwChar.readValue();
        const keyStr = GAN_ENCRYPTION_KEYS[(version >> 8) & 0xff];
        if (!keyStr) {
            throw new Error("Unsupported GAN cube: unknown encryption key for version " + version.toString(16));
        }
        let key = JSON.parse(LZString.decompressFromEncodedURIComponent(keyStr));
        for (let i = 0; i < 6; i++) {
            key[i] = (key[i] + hwVal.getUint8(5 - i)) & 0xff;
        }
        ganDecoder = new aes128(key);
    }

    ganPrevMoveCount = -1;
    const cubeService = await server.getPrimaryService(GAN_SERVICE_UUID);
    const cubeChar    = await cubeService.getCharacteristic(GAN_CHARACTERISTIC_UUID);
    await cubeChar.startNotifications();
    cubeChar.addEventListener("characteristicvaluechanged", GanNotifications);
}

async function connectGiiker(server) {
    const cubeService = await server.getPrimaryService(GIIKER_SERVICE_UUID);
    const cubeChar    = await cubeService.getCharacteristic(GIIKER_CHARACTERISTIC_UUID);
    await cubeChar.startNotifications();
    cubeChar.addEventListener("characteristicvaluechanged", GiikerNotifications);
}

async function connectGoCube(server) {
    const cubeService = await server.getPrimaryService(GOCUBE_SERVICE_UUID);
    const cubeChar    = await cubeService.getCharacteristic(GOCUBE_CHARACTERISTIC_UUID);
    await cubeChar.startNotifications();
    cubeChar.addEventListener("characteristicvaluechanged", GoNotifications);
}

function GanNotifications(event) {
    try {
        let data = new Uint8Array(event.target.value.buffer);
        if (ganDecoder) {
            data = ganDecoder.decode(data, data.length);
        }
        const moveCount = data[12] & 0xff;
        if (ganPrevMoveCount === -1) {
            ganPrevMoveCount = moveCount;
            return;
        }
        const newCount = ((moveCount - ganPrevMoveCount) + 256) % 256;
        ganPrevMoveCount = moveCount;
        // Moves are packed 5 bits each, newest-first, starting at byte 13
        for (let i = newCount - 1; i >= 0; i--) {
            const bitOffset = i * 5;
            const byteIdx   = 13 + (bitOffset >> 3);
            const bitShift  = bitOffset & 7;
            const moveIdx   = ((data[byteIdx] | (data[byteIdx + 1] << 8)) >> bitShift) & 0x1f;
            if (moveIdx < GAN_MOVES.length) {
                const turn = GAN_MOVES[moveIdx];
                $("g-cube").gscramble(turn);
                sendMove(turn);
            }
        }
    } catch (ex) {
        console.error("GAN notification error:", ex);
    }
}

function GoNotifications(event) {
    try {
        const val = event.target.value;
        // Packet: byte 0 = type, byte 1 = payload length (6), byte 3 = move index
        if (val.byteLength === 8 && val.getUint8(1) === 6) {
            const turn = ["B", "B'", "F", "F'", "U", "U'", "D", "D'", "R", "R'", "L", "L'"][val.getUint8(3)];
            if (turn !== undefined) {
                $("g-cube").gscramble(turn);
                sendMove(turn);
            }
        }
    } catch (ex) {
        console.error("GoCube notification error:", ex);
    }
}

let giikerFirst = true;
function GiikerNotifications(event) {
    if (giikerFirst) {
        giikerFirst = false;
        return; // skip first event (contains current state, not a move)
    }
    try {
        const val   = event.target.value;
        const state = [];
        if (val.getUint8(18) === 0xa7) { // encrypted
            const key = [176, 81, 104, 224, 86, 137, 237, 119, 38, 26, 193, 161, 210, 126,
                         150, 81, 93, 13, 236, 249, 89, 235, 88, 24, 113, 81, 214, 131,
                         130, 199, 2, 169, 39, 165, 171, 41];
            const k  = val.getUint8(19);
            const k1 = (k >> 4) & 0xf;
            const k2 = k & 0xf;
            for (let i = 0; i < 20; i++) {
                const v = (val.getUint8(i) + key[i + k1] + key[i + k2]) & 0xff;
                state.push((v >> 4) & 0xf);
                state.push(v & 0xf);
            }
        } else {
            for (let i = 0; i < 20; i++) {
                const v = val.getUint8(i);
                state.push((v >> 4) & 0xf);
                state.push(v & 0xf);
            }
        }
        const face   = state[32];
        const amount = state[33];
        const turn   = ["?", "B", "D", "L", "U", "R", "F"][face]
                     + ["", "", "2", "'"][amount === 9 ? 2 : amount];
        $("g-cube").gscramble(turn);
        sendMove(turn);
    } catch (ex) {
        console.error("Giiker notification error:", ex);
    }
}
