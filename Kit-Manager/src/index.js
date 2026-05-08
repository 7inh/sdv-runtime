// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

const express = require('express');
const fs = require('fs');
const path = require('path');
const http = require('http');
const { Server } = require('socket.io');
const config = require('../configs');
const convertPgCode = require('./convert_code');
const cors = require('cors')

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
const server = http.createServer(app); 
const io = new Server(server, {
    maxHttpBufferSize: 1e8,
    cors: {
        origin: '*',
    }
});

let KITS = new Map()
let CLIENTS = new Map()
let SYNCER_HW = new Map()

const LOG_PREFIX = '[KitManager]'

function formatMetaValue(value) {
    if (value === undefined || value === null) return String(value)
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
        return String(value)
    }
    try {
        return JSON.stringify(value)
    } catch (error) {
        return '[unserializable]'
    }
}

function log(level, event, meta = {}) {
    const ts = new Date().toISOString()
    const metaStr = Object.entries(meta)
        .map(([key, value]) => `${key}=${formatMetaValue(value)}`)
        .join(' ')
    const line = `${ts} ${LOG_PREFIX} [${event}]${metaStr ? ` ${metaStr}` : ''}`

    if (level === 'error') {
        console.error(line)
    } else if (level === 'warn') {
        console.warn(line)
    } else {
        console.log(line)
    }
}

process.on('uncaughtException', (err) => {
    log('error', 'UNCAUGHT_EXCEPTION', {
        error: err?.message || String(err),
        stack: err?.stack,
    })
})

process.on('unhandledRejection', (reason) => {
    log('error', 'UNHANDLED_REJECTION', {
        reason: reason?.message || String(reason),
        stack: reason?.stack,
    })
})

io.engine.on('connection_error', (err) => {
    log('warn', 'SOCKET_HANDSHAKE_FAILED', {
        code: err.code,
        message: err.message,
        context: err.context && JSON.stringify(err.context).slice(0, 200),
        remote: err.req?.socket?.remoteAddress || '',
    })
})

function countOnlineItems(itemMap) {
    let online = 0
    itemMap.forEach((item) => {
        if (item.is_online) online += 1
    })
    return online
}

const NOISY_FORWARD_CMDS = new Set(
    (process.env.KIT_LOG_QUIET_CMDS || 'get-runtime-info,subscribe_apis,unsubscribe_apis')
        .split(',').map(s => s.trim()).filter(Boolean)
)

function summarizeMap(itemMap, max = 20) {
    const parts = []
    let i = 0
    for (const item of itemMap.values()) {
        if (i >= max) {
            parts.push(`(+${itemMap.size - max} more)`)
            break
        }
        parts.push(`${item.kit_id}:${item.is_online ? 'on' : 'off'}`)
        i += 1
    }
    return parts.join(',')
}

// setInterval(() => {
//     console.log(`KITS: ${KITS.size}`)
//     KITS.forEach((kit, kit_id) => {
//         console.log(`Kit ${kit_id} is online: ${kit.is_online}`)
//     })

//     console.log(`CLIENTS: ${CLIENTS.size}`)
//     CLIENTS.forEach((client, client_id) => {
//         console.log(`Client ${client_id} is online: ${client.is_online}`)
//     })
// }, 3000)

let hasKitStateChange = false
let hasHwStateChange = false

app.use(cors({
    origin: '*'
}));

app.get('/listAllKits', (req, res) => {
    return res.json({
        status: "OK",
        message: "List all kits",
        content: Array.from(KITS.values())
    })
});

app.get('/listAllClient', (req, res) => {
    return res.json({
        status: "OK",
        message: "List all clients",
        content: Array.from(CLIENTS.values())
    })
});

app.post('/convertCode', async (req, res) => {
    if(!req.body.code) {
        return res.json({
                status: "ERR",
                message: "Missing code",
        })
    }
    try {
        const convertedCode = await convertPgCode('VehicleApp', req.body.code || '')
        return res.json({
            status: "OK",
            message: "Successful",
            content: convertedCode
        })
    } catch (error) {
        log('error', 'CONVERT_CODE_HTTP_FAILED', {
            error: error?.message || String(error),
        })
        return res.status(500).json({
            status: 'ERR',
            message: 'Code conversion failed',
        })
    }
})

function announceListOfKit() {
    CLIENTS.forEach((client, client_id) => {
        io.to(client_id).emit('list-all-kits-result', Array.from(KITS.values()))
    })
    hasKitStateChange = false
    log('info', 'KIT_LIST_CHANGED', {
        totalKits: KITS.size,
        onlineKits: countOnlineItems(KITS),
        kits: summarizeMap(KITS),
    })
}

function announceListOfHw() {
    CLIENTS.forEach((client, client_id) => {
        io.to(client_id).emit('list-all-hw-result', Array.from(SYNCER_HW.values()))
    })
    hasHwStateChange = false
    log('info', 'SYNCER_HW_LIST_CHANGED', {
        totalSyncerHw: SYNCER_HW.size,
        onlineSyncerHw: countOnlineItems(SYNCER_HW),
        syncerHw: summarizeMap(SYNCER_HW),
    })
}

setInterval(() => {
        if(hasKitStateChange) {
                announceListOfKit()
        }
        if(hasHwStateChange) {
                announceListOfHw()
        }
}, 1000)

setInterval(() => {
    const totalKits = KITS.size
    const onlineKits = countOnlineItems(KITS)
    const totalSyncerHw = SYNCER_HW.size
    const onlineSyncerHw = countOnlineItems(SYNCER_HW)
    log('info', 'HEARTBEAT', {
        totalKits,
        onlineKits,
        offlineKits: totalKits - onlineKits,
        totalSyncerHw,
        onlineSyncerHw,
        offlineSyncerHw: totalSyncerHw - onlineSyncerHw,
        totalClients: CLIENTS.size,
        hasKitStateChange,
        kits: summarizeMap(KITS),
        syncerHw: summarizeMap(SYNCER_HW),
    })
}, 10000)

io.on('connection', (socket) => {
    log('info', 'SOCKET_CONNECTED', { socketId: socket.id })

    socket.on('error', (err) => {
        log('warn', 'SOCKET_ERROR', {
            socketId: socket.id,
            error: err?.message || String(err),
        })
    })
    /**
     * Register a kit
     */
    socket.on('register_kit', (payload) => {
        if(!payload || !payload.kit_id) {
            log('warn', 'REGISTER_KIT_INVALID_PAYLOAD', { socketId: socket.id })
            return;
        }
        KITS.set(payload.kit_id, {
            socket_id: socket.id,
            kit_id: payload.kit_id,
            name: payload.name || '',
            last_seen: new Date().getTime(),
            is_online: true,
            noRunner: 0,
            noSubscriber: 0,
            support_apis: payload.support_apis || [],
            desc: payload.desc || '',
        })
        hasKitStateChange = true
        log('info', 'REGISTER_KIT', {
            socketId: socket.id,
            kitId: payload.kit_id,
            name: payload.name || '',
            supportApiCount: (payload.support_apis || []).length,
            totalKits: KITS.size,
            onlineKits: countOnlineItems(KITS),
        })
    })

    socket.on('register_hw_kit', (payload) => {
        if(!payload || !payload.kit_id) {
            log('warn', 'REGISTER_SYNCER_HW_INVALID_PAYLOAD', { socketId: socket.id })
            return;
        }
        SYNCER_HW.set(payload.kit_id, {
            socket_id: socket.id,
            kit_id: payload.kit_id,
            name: payload.name || '',
            last_seen: new Date().getTime(),
            is_online: true,
            support_apis: payload.support_apis || [],
            desc: payload.desc || '',
        })
        hasHwStateChange = true
        log('info', 'REGISTER_SYNCER_HW', {
            socketId: socket.id,
            kitId: payload.kit_id,
            name: payload.name || '',
            supportApiCount: (payload.support_apis || []).length,
            totalSyncerHw: SYNCER_HW.size,
            onlineSyncerHw: countOnlineItems(SYNCER_HW),
        })
    })

    socket.on('report-runtime-state', (payload) => {
        let kit_id = payload?.kit_id || null
        if(kit_id && payload.data) {
            let kit = KITS.get(kit_id)
            if(!kit) {
                log('warn', 'REPORT_RUNTIME_STATE_UNKNOWN_KIT', { socketId: socket.id, kitId: kit_id })
                return
            }
            kit.noRunner = payload.data.noOfRunner || 0
            kit.noSubscriber = payload.data.noSubscriber || 0
            KITS.set(kit_id, kit)
            hasKitStateChange = true
        }
    })

    /**
     * Register a client
     */
    socket.on('register_client', (payload) => {
        if(!payload) {
            log('warn', 'REGISTER_CLIENT_INVALID_PAYLOAD', { socketId: socket.id })
            return;
        }
        CLIENTS.set(socket.id, {
            username: payload.username,
            user_id: payload.user_id,
            domain: payload.domain,
            last_seen: new Date().getTime(),
            is_online: true,
        })
        log('info', 'REGISTER_CLIENT', {
            socketId: socket.id,
            userId: payload.user_id || '',
            username: payload.username || '',
            domain: payload.domain || '',
            totalClients: CLIENTS.size,
        })
        socket.emit('list-all-kits-result', Array.from(KITS.values()))
        socket.emit('list-all-hw-result', Array.from(SYNCER_HW.values()))
    });

    socket.on('unregister_client', (payload) => {
        let existClient = CLIENTS.get(socket.id)
        if(existClient) {
            CLIENTS.delete(socket.id)
            log('info', 'UNREGISTER_CLIENT', {
                socketId: socket.id,
                userId: existClient.user_id || '',
                username: existClient.username || '',
                payloadReason: payload?.reason || '',
                totalClients: CLIENTS.size,
            })
        } else {
            log('warn', 'UNREGISTER_CLIENT_NOT_FOUND', { socketId: socket.id })
        }
    });

    socket.on('clientSubscribeToKit', (payload) => {
        if(!payload || !payload.kit_id) {
            log('warn', 'SUBSCRIBE_INVALID_PAYLOAD', {
                socketId: socket.id,
                hasPayload: Boolean(payload),
            })
            return;
        }
        socket.join(payload.kit_id)
    });

    socket.on('clientUnsubscribeToKit', (payload) => {
        if(!payload || !payload.kit_id) {
            log('warn', 'UNSUBSCRIBE_INVALID_PAYLOAD', {
                socketId: socket.id,
                hasPayload: Boolean(payload),
            })
            return;
        }
        socket.leave(payload.kit_id)
    });


    socket.on('list-all-kits', () => {
        log('info', 'LIST_ALL_KITS_REQUEST', { socketId: socket.id, totalKits: KITS.size })
        socket.emit('list-all-kits-result', Array.from(KITS.values()))
    });

    socket.on('list-all-syncer_hw', () => {
        log('info', 'LIST_ALL_SYNCER_HW_REQUEST', { socketId: socket.id, totalSyncerHw: SYNCER_HW.size })
        socket.emit('list-all-hw-result', Array.from(SYNCER_HW.values()))
    });

    /**
     * Handle disconnection
     */
     socket.on('disconnect', (reason) => {
        // --------------------------------------------
        let existKit = Array.from(KITS.values()).find(kit => kit.socket_id == socket.id)
        if(existKit) {
            existKit.is_online = false
            existKit.last_seen = new Date().getTime()
            hasKitStateChange = true
            log('info', 'KIT_DISCONNECTED', {
                socketId: socket.id,
                kitId: existKit.kit_id,
                reason,
                totalKits: KITS.size,
                onlineKits: countOnlineItems(KITS),
            })
            announceListOfKit()
        }
        //---------------------------------------------
        let existSyncerHW = Array.from(SYNCER_HW.values()).find(hw => hw.socket_id == socket.id)
        if(existSyncerHW) {
            existSyncerHW.is_online = false
            existSyncerHW.last_seen = new Date().getTime()
            hasHwStateChange = true
            log('info', 'SYNCER_HW_DISCONNECTED', {
                socketId: socket.id,
                kitId: existSyncerHW.kit_id,
                reason,
                totalSyncerHw: SYNCER_HW.size,
                onlineSyncerHw: countOnlineItems(SYNCER_HW),
            })
        }
        // --------------------------------------------
        let existClient = CLIENTS.get(socket.id)
        if(existClient) {
            CLIENTS.delete(socket.id)
            log('info', 'CLIENT_DISCONNECTED', {
                socketId: socket.id,
                userId: existClient.user_id || '',
                username: existClient.username || '',
                reason,
                totalClients: CLIENTS.size,
            })
        }
        if(!existKit && !existSyncerHW && !existClient) {
            log('warn', 'SOCKET_DISCONNECTED_UNKNOWN_ACTOR', { socketId: socket.id, reason })
        }
    });

    // ------------ MESSAGE FROM CLIENT TO KIT ----------------
    socket.on('messageToKit', async (payload) => {
        if(!payload || !payload.cmd || !payload.to_kit_id) {
            log('warn', 'MESSAGE_TO_KIT_INVALID_PAYLOAD', {
                socketId: socket.id,
                hasPayload: Boolean(payload),
                cmd: payload?.cmd,
                toKitId: payload?.to_kit_id,
            })
            return;
        }
        let kit = KITS.get(payload.to_kit_id)
        if(kit) {
            if(["deploy_request", "deploy_n_run"].includes(payload.cmd)) {
                let convertedCode =  ''
                try {
                    if(payload.disable_code_convert) {
                        convertedCode = payload.code
                    } else {
                        convertedCode = await convertPgCode(payload.prototype?.name || 'App', payload.code || '')
                    }
                } catch (error) {
                    log('error', 'MESSAGE_TO_KIT_CODE_CONVERT_FAILED', {
                        socketId: socket.id,
                        cmd: payload.cmd,
                        toKitId: payload.to_kit_id,
                        requestFrom: socket.id,
                        error: error?.message || String(error),
                    })
                    io.to(socket.id).emit('messageToKit-kitReply', {
                        status: 'ERR',
                        cmd: payload.cmd,
                        to_kit_id: payload.to_kit_id,
                        request_from: socket.id,
                        message: 'Code conversion failed',
                    })
                    return
                }
                if (!NOISY_FORWARD_CMDS.has(payload.cmd)) {
                    log('info', 'MESSAGE_TO_KIT_FORWARD', {
                        socketId: socket.id,
                        cmd: payload.cmd,
                        toKitId: payload.to_kit_id,
                        requestFrom: socket.id,
                        converted: true,
                    })
                }
                io.to(kit.socket_id).emit('messageToKit', {
                    request_from: socket.id,
                    ...payload,
                    convertedCode: convertedCode
                })
            } else {
                if (!NOISY_FORWARD_CMDS.has(payload.cmd)) {
                    log('info', 'MESSAGE_TO_KIT_FORWARD', {
                        socketId: socket.id,
                        cmd: payload.cmd,
                        toKitId: payload.to_kit_id,
                        requestFrom: socket.id,
                        converted: false,
                    })
                }
                io.to(kit.socket_id).emit('messageToKit', {
                    request_from: socket.id,
                    ...payload
                })
            }
        } else {
            log('warn', 'MESSAGE_TO_KIT_TARGET_NOT_FOUND', {
                socketId: socket.id,
                cmd: payload.cmd,
                toKitId: payload.to_kit_id,
                requestFrom: socket.id,
            })
        }
    })
    socket.on('messageToKit-kitReply', (payload) => {
        if(!payload || !payload.request_from) {
            log('warn', 'MESSAGE_TO_KIT_REPLY_INVALID_PAYLOAD', {
                socketId: socket.id,
                hasPayload: Boolean(payload),
            })
            return;
        }
        if (!NOISY_FORWARD_CMDS.has(payload.cmd)) {
            log('info', 'MESSAGE_TO_KIT_REPLY_FORWARD', {
                socketId: socket.id,
                cmd: payload.cmd || '',
                requestTo: payload.request_from,
            })
        }
        io.to(payload.request_from).emit('messageToKit-kitReply', payload)
    })

    // ------------ MESSAGE FROM KIT TO CLIENT ----------------
    socket.on('broadcastToClient', (payload) => {
        if(!payload || !payload.cmd || payload.kit_id) {
            log('warn', 'BROADCAST_TO_CLIENT_INVALID', {
                socketId: socket.id,
                hasPayload: Boolean(payload),
                cmd: payload?.cmd,
                kitId: payload?.kit_id,
            })
            return;
        }
        let kit = KITS.get(payload.kit_id)
        if(kit && kit.socket_id == socket.id) {
            io.to(payload.kit_id).emit('broadcastToClient', payload) 
        } else {
            log('warn', 'BROADCAST_TO_CLIENT_INVALID', {
                socketId: socket.id,
                cmd: payload.cmd,
                kitId: payload.kit_id,
                reason: kit ? 'socket_owner_mismatch' : 'kit_not_found',
            })
        }
    })

    // ------------ MESSAGE FROM CLIENT TO KIT ----------------
    socket.on('messageToSyncerHw', (payload) => {
        if(!payload || !payload.cmd || !payload.to_kit_id) {
            log('warn', 'MESSAGE_TO_SYNCER_HW_INVALID_PAYLOAD', {
                socketId: socket.id,
                hasPayload: Boolean(payload),
                cmd: payload?.cmd,
                toKitId: payload?.to_kit_id,
            })
            return;
        }
        if(payload.cmd == 'syncer_set') {
            let kit = SYNCER_HW.get(payload.to_kit_id)
            if(kit) {
                log('info', 'MESSAGE_TO_SYNCER_HW_FORWARD', {
                    socketId: socket.id,
                    cmd: payload.cmd,
                    toKitId: payload.to_kit_id,
                    requestFrom: socket.id,
                })
                io.to(kit.socket_id).emit('messageToSyncerHw', {
                    request_from: socket.id,
                    ...payload
                })
            } else {
                log('warn', 'MESSAGE_TO_SYNCER_HW_TARGET_NOT_FOUND', {
                    socketId: socket.id,
                    cmd: payload.cmd,
                    toKitId: payload.to_kit_id,
                    requestFrom: socket.id,
                })
            }
        } else {
            log('warn', 'MESSAGE_TO_SYNCER_HW_UNSUPPORTED_CMD', {
                socketId: socket.id,
                cmd: payload.cmd,
                toKitId: payload.to_kit_id,
            })
        }
    })
    socket.on('messageToSyncerHw-kitReply', (payload) => {
        if(!payload || !payload.request_from) {
            log('warn', 'MESSAGE_TO_SYNCER_HW_REPLY_INVALID_PAYLOAD', {
                socketId: socket.id,
                hasPayload: Boolean(payload),
            })
            return;
        }
        log('info', 'MESSAGE_TO_SYNCER_HW_REPLY_FORWARD', {
            socketId: socket.id,
            cmd: payload.cmd || '',
            requestTo: payload.request_from,
        })
        io.to(payload.request_from).emit('messageToKit-kitReply', payload)
    })

});

server.listen(config.port, () => {
    log('info', 'SERVER_STARTED', { port: config.port });
});

server.on('error', (err) => {
    log('error', 'HTTP_SERVER_ERROR', {
        error: err?.message,
        code: err?.code,
    })
})