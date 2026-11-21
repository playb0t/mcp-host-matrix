import { createInterface } from 'node:readline';

const delay = Number(process.argv[2] ?? 45000);
if (!Number.isSafeInteger(delay) || delay < 1 || delay > 300000) {
  throw new Error('Delay must be an integer between 1 and 300000 milliseconds');
}
let changed = false;
let scheduled = false;
const send = message => process.stdout.write(JSON.stringify({ jsonrpc: '2.0', ...message }) + '\n');
const tool = name => ({ name, description: name, inputSchema: { type: 'object', properties: {} } });
const input = createInterface({ input: process.stdin });
input.on('line', line => {
  let request;
  try { request = JSON.parse(line); } catch { return; }
  if (request.method === 'notifications/initialized' && !scheduled) {
    scheduled = true;
    setTimeout(() => {
      changed = true;
      send({ method: 'notifications/tools/list_changed' });
    }, delay).unref();
    return;
  }
  if (request.id === undefined) { return; }
  switch (request.method) {
    case 'initialize':
      send({ id: request.id, result: {
        protocolVersion: request.params.protocolVersion,
        capabilities: { tools: { listChanged: true } },
        serverInfo: { name: 'tool-catalog-repro', version: '1.0.0' }
      } });
      break;
    case 'ping': send({ id: request.id, result: {} }); break;
    case 'tools/list':
      send({ id: request.id, result: { tools: [tool('matching_keep'), tool(changed ? 'matching_added' : 'matching_removed')] } });
      break;
    case 'tools/call': send({ id: request.id, result: { content: [{ type: 'text', text: 'ok' }] } }); break;
    default: send({ id: request.id, error: { code: -32601, message: 'Method not found' } });
  }
});
