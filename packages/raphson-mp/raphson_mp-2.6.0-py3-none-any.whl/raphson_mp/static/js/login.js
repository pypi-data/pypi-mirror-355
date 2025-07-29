document.getElementById("webauthn-login").addEventListener("click", async () => {
    // https://developer.mozilla.org/en-US/docs/Web/API/PublicKeyCredentialRequestOptions
    const options = {
        challenge: Uint8Array.from(document.getElementById('webauthn-challenge').textContent, c => c.charCodeAt(0)),
    };

    const credential = await navigator.credentials.get({ publicKey: options });

    if (credential == null) {
        return;
    }


    const response = /** @type {AuthenticatorAssertionResponse} */ (/** @type {PublicKeyCredential} */ (credential).response);

    // https://developer.mozilla.org/en-US/docs/Web/API/AuthenticatorResponse/clientDataJSON
    const clientDataJsonB64 = btoa(String.fromCharCode(...new Uint8Array(response.clientDataJSON)));
    // https://developer.mozilla.org/en-US/docs/Web/API/AuthenticatorAssertionResponse/authenticatorData
    const authenticatorDataB64 = btoa(String.fromCharCode(...new Uint8Array(response.authenticatorData)));
    // https://developer.mozilla.org/en-US/docs/Web/API/AuthenticatorAssertionResponse/signature
    const signatureB64 = btoa(String.fromCharCode(...new Uint8Array(response.signature)));
    // https://developer.mozilla.org/en-US/docs/Web/API/AuthenticatorAssertionResponse/userHandle
    const userHandleB64 = String.fromCharCode(...new Uint8Array(response.userHandle));

    const fetchOptions = {
        method: 'POST',
        body: JSON.stringify({ authenticator_data: authenticatorDataB64, client_data: clientDataJsonB64, signature: signatureB64, user_handle: userHandleB64 }),
        headers: new Headers({
            'Content-Type': 'application/json'
        }),
    };
    const fetchResponse = await fetch(new Request("/auth/webauthn_login", fetchOptions));
    if (fetchResponse.status == 204) {
        window.location.assign('/');
    }
});
