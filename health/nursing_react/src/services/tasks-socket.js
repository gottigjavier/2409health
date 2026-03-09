    //----------- Tasks Section websocket - channel through consumer.py -----------
    import { getWsUrl } from './websocket'

    export const tasksManager = ({handleTasks}) => {
        const wsUrl = getWsUrl('/ws/taskData/')
        const call = new WebSocket(wsUrl);
            call.onopen = () => {
                console.log('Tasks connected');
            };

            call.onmessage = e => {
                try {
                    const msg = JSON.parse(e.data);
                    console.debug('WS tasks message received', { tasks: msg.tasks ? msg.tasks.length : undefined });
                    handleTasks(msg);
                } catch (err) {
                    console.error('Failed parsing tasks WS message', err, e.data);
                }
            };

            call.onerror = e => {
                console.log('Tasks WS error:', e);
            };

            call.onclose = e => {
                console.log('Tasks closed:', e.code, e.reason);
            };

        return call;
    }
    // -------- End Tasks section websocket - channel -------------------
