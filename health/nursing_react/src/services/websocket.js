const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

const getToken = () => localStorage.getItem('access_token');

export const getWsUrl = (path) => {
  const token = getToken();
  if (token) {
    return `${WS_URL}${path}?token=${token}`;
  }
  return `${WS_URL}${path}`;
};

export const appManager = ({ handleApp }) => {
  const wsUrl = getWsUrl('/ws/appData/');
  const call = new WebSocket(wsUrl);
  
  call.onopen = () => {
    console.log('App connected');
  };

  call.onmessage = e => {
    const msg = JSON.parse(e.data);
    handleApp(msg);
  };

  call.onerror = e => {
    console.log('WebSocket error:', e);
  };

  call.onclose = e => {
    console.log('App closed:', e.code, e.reason);
  };

  return call;
};

export const callManager = ({ handleCall }) => {
  const wsUrl = getWsUrl('/ws/callData/');
  const call = new WebSocket(wsUrl);

  call.onopen = () => {
    console.log('Calls connected');
  };

  call.onmessage = e => {
    const msg = JSON.parse(e.data);
    handleCall(msg);
  };

  call.onerror = e => {
    console.log('WebSocket error:', e);
  };

  call.onclose = e => {
    console.log('Calls closed:', e.code, e.reason);
  };

  return call;
};

export const taskManager = ({ handleTasks }) => {
  const wsUrl = getWsUrl('/ws/taskData/');
  const call = new WebSocket(wsUrl);

  call.onopen = () => {
    console.log('Tasks connected');
  };

  call.onmessage = e => {
    const msg = JSON.parse(e.data);
    handleTasks(msg);
  };

  call.onerror = e => {
    console.log('WebSocket error:', e);
  };

  call.onclose = e => {
    console.log('Tasks closed:', e.code, e.reason);
  };

  return call;
};
