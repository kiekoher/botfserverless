function prefix(userId) {
  return `whatsapp:${userId}`;
}

function qrKey(userId) {
  return `${prefix(userId)}:qr_code`;
}

function statusKey(userId) {
  return `${prefix(userId)}:status`;
}

module.exports = { qrKey, statusKey };
