import type { WsMessage } from "../types/sim";

export function createEventsSocket(onMessage: (msg: WsMessage) => void): WebSocket {
  const scheme = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${scheme}://${window.location.host}/ws/events`);

  socket.onmessage = (ev: MessageEvent<string>) => {
    try {
      const parsed = JSON.parse(ev.data) as WsMessage;
      onMessage(parsed);
    } catch {
      // Ignore malformed messages in demo mode.
    }
  };

  socket.onopen = () => {
    socket.send("subscribe");
  };

  return socket;
}
