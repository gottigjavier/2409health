    //----------- App Section websocket - channel through consumer.py -----------
    import { getWsUrl } from './websocket'

    export const appManager = ({handleApp}) => {
        const wsUrl = getWsUrl('/ws/appData/')
        const call = new WebSocket(wsUrl);
            call.onopen = () => {
                console.log('App connected');
            };

            call.onmessage = e => {
                try {
                    const msg = JSON.parse(e.data);
                    console.debug('WS app message received', { beds: msg.beds ? msg.beds.length : undefined, calls: msg.calls ? msg.calls.length : undefined, tasks: msg.tasks ? msg.tasks.length : undefined });
                    handleApp(msg);
                } catch (err) {
                    console.error('Failed parsing app WS message', err, e.data);
                }
            };

            call.onerror = e => {
                console.log('App WS error:', e);
            };

            call.onclose = e => {
                console.log('App closed:', e.code, e.reason);
            };

        return call;
    }
    // -------- End App section websocket - channel -------------------
