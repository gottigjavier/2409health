    //----------- Calls Section websocket - channel through consumer.py ------------
    import { getWsUrl } from './websocket'

    export const callsManager = ({handleCall}) => {
        const wsUrl = getWsUrl('/ws/callData/')
        const call = new WebSocket(wsUrl);
            call.onopen = () => {
                console.log('Calls connected');
            };

            call.onmessage = e => {
                try {
                    const msg = JSON.parse(e.data);
                    console.debug('WS calls message received', { hasCall: !!msg.call, state: msg.state });
                    handleCall(msg);
                } catch (err) {
                    console.error('Failed parsing calls WS message', err, e.data);
                }
            };

            call.onerror = e => {
                console.log('Calls WS error:', e);
            };

            call.onclose = e => {
                console.log('Calls closed:', e.code, e.reason);
            };

        // return socket so caller can close it if needed
        return call;
    }
    //---------------- End Calls Section websocket ------------------------------
