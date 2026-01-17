document.addEventListener('DOMContentLoaded', () => {
    const hashInput = document.getElementById('hash-input');
    const hashOutput = document.getElementById('hash-output');

    if (hashInput && hashOutput) {
        hashInput.addEventListener('input', async (e) => {
            const text = e.target.value;
            if (!text) {
                hashOutput.innerText = "Waiting for input...";
                return;
            }
            
            // Use Web Crypto API for client-side hashing demo
            const msgBuffer = new TextEncoder().encode(text);
            const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
            
            hashOutput.innerText = hashHex;
        });
    }
});
