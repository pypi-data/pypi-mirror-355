use core_common::{
    Result,
    constants::{AES_KEY_LEN, AES_NONCE_LEN},
    error,
};

// Performs the encryption and decryption in untrusted mode.
#[cfg(not(target_vendor = "teaclave"))]
pub(crate) mod untrusted {
    use super::*;
    use aes_gcm::{Aes128Gcm, Key, KeyInit, Nonce, aead::AeadInPlace};
    pub fn do_encrypt(
        ciphertext: &mut Vec<u8>,
        key_fixed_bytes: [u8; AES_KEY_LEN],
        nonce_fixed_bytes: [u8; AES_NONCE_LEN],
    ) -> Result<()> {
        let key = Key::<Aes128Gcm>::from_slice(&key_fixed_bytes);
        let cipher: Aes128Gcm = Aes128Gcm::new(key);
        let nonce = Nonce::from(nonce_fixed_bytes);
        cipher
            .encrypt_in_place(&nonce, b"", ciphertext)
            .map_err(|source| error!("{:?}", source))?;
        Ok(())
    }

    pub fn do_decrypt(
        ciphertext: &mut Vec<u8>,
        key_fixed_bytes: [u8; AES_KEY_LEN],
        nonce_fixed_bytes: [u8; AES_NONCE_LEN],
    ) -> Result<()> {
        let key = Key::<Aes128Gcm>::from_slice(&key_fixed_bytes);
        // Set to software mode in Cargo.toml. The default behavior causes the operator
        //  to silently crash here:
        let cipher: Aes128Gcm = Aes128Gcm::new(key);
        let nonce = Nonce::from(nonce_fixed_bytes);
        // Decrypt `buffer` in-place, replacing its ciphertext context with the original plaintext
        cipher
            .decrypt_in_place(&nonce, b"", ciphertext)
            .map_err(|source| error!(source))?;
        Ok(())
    }
}

#[cfg(target_vendor = "teaclave")]
pub(crate) mod trusted {
    use super::*;
    use core_common::constants::AES_TAG_LEN;
    use sgx_crypto::aes::gcm::{Aad, AesGcm};
    use sgx_types::types::Mac128bit;

    pub fn do_encrypt(
        ciphertext: &mut Vec<u8>,
        key_fixed_bytes: [u8; AES_KEY_LEN],
        nonce_fixed_bytes: [u8; AES_NONCE_LEN],
    ) -> Result<()> {
        let aad = Aad::empty();
        let mut cipher = AesGcm::new(&key_fixed_bytes, nonce_fixed_bytes.into(), aad)
            .map_err(|source| error!("{:?}", source))?;

        let mac = cipher
            .encrypt_in_place(ciphertext.as_mut())
            .map_err(|source| error!("{:?}", source))?;
        ciphertext.extend_from_slice(&mac);
        Ok(())
    }

    pub fn do_decrypt(
        ciphertext: &mut Vec<u8>,
        key_fixed_bytes: [u8; AES_KEY_LEN],
        nonce_fixed_bytes: [u8; AES_NONCE_LEN],
    ) -> Result<()> {
        let aad = Aad::empty();
        let mut cipher = AesGcm::new(&key_fixed_bytes, nonce_fixed_bytes.into(), aad)
            .map_err(|source| error!("{:?}", source))?;
        let mac = ciphertext.split_off(ciphertext.len() - AES_TAG_LEN);
        let mut mac_bytes: Mac128bit = [0; AES_TAG_LEN];
        mac_bytes.copy_from_slice(&mac);
        cipher
            .decrypt_in_place(ciphertext.as_mut(), &mut mac_bytes)
            .map_err(|source| error!("{:?}", source))?;
        Ok(())
    }
}
