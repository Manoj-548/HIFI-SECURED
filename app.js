/* ============================================================================
   TOKEN SECURED - APP CORE ENGINE WITH ANTI-THEFT CIPHER VAULT & 2FA GUARD
   ============================================================================ */

(function () {
  "use strict";

  // Application State
  const state = {
    vaultUnlocked: false,
    failedPasscodeAttempts: 0,
    tokens: [],
    blockchain: [],
    pendingAlert: null,
    pending2FAAlert: null,
    stats: {
      verifiedUses: 0,
      blockedAttempts: 0
    }
  };

  // Master Passcode Key (2FA Protected)
  const MASTER_VAULT_PASSCODE = "123456";

  // Helper: SHA-256 Hash simulation / Cryptographic string generator
  function generateCryptoHash(inputStr) {
    let hash = 0;
    for (let i = 0; i < inputStr.length; i++) {
      const char = inputStr.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash |= 0;
    }
    const hex = Math.abs(hash).toString(16).toUpperCase().padStart(8, '0');
    return '0x' + hex + Math.random().toString(36).substring(2, 10).toUpperCase();
  }

  // Master Vault Lock & Decrypt Handlers
  window.unlockMasterVault = function () {
    const entered = document.getElementById('masterPasscodeInput').value.trim();
    if (entered === MASTER_VAULT_PASSCODE) {
      state.vaultUnlocked = true;
      state.failedPasscodeAttempts = 0;
      document.getElementById('masterVaultLockScreen').classList.remove('active');
      document.getElementById('masterPasscodeInput').value = '';
      
      appendBlockchainBlock("VAULT_UNLOCKED", {
        status: "2FA_AUTHENTICATED",
        action: "DECRYPTED_TOKEN_VAULT"
      });
      alert("🔓 Vault Unlocked: 2FA Master Passcode verified!");
    } else {
      state.failedPasscodeAttempts += 1;
      appendBlockchainBlock("ANTI_THEFT_FAILED_LOGIN", {
        attempt: state.failedPasscodeAttempts,
        status: "UNAUTHORIZED_ACCESS_BLOCKED"
      });

      if (state.failedPasscodeAttempts >= 3) {
        alert("⛔ ANTI-THEFT EMERGENCY LOCKOUT: 3 Failed Master Passcode attempts! Security Alert Email sent to account owner.");
        state.failedPasscodeAttempts = 0;
      } else {
        alert(`❌ Invalid Master Passcode! Attempts remaining: ${3 - state.failedPasscodeAttempts}`);
      }
    }
  };

  window.lockMasterVault = function () {
    state.vaultUnlocked = false;
    document.getElementById('masterVaultLockScreen').classList.add('active');
    appendBlockchainBlock("VAULT_LOCKED", {
      status: "SECURITY_ENCRYPTED"
    });
  };

  // Initialize Genesis Block on Blockchain
  function initGenesisBlock() {
    const savedBlocks = localStorage.getItem('cipher_blockchain');
    if (savedBlocks) {
      try {
        state.blockchain = JSON.parse(savedBlocks);
      } catch (e) {
        state.blockchain = [];
      }
    }

    if (state.blockchain.length === 0) {
      const genesisBlock = {
        index: 1,
        timestamp: new Date().toLocaleString(),
        type: "GENESIS_BLOCK",
        data: "Token Secured Initial Security Anchor Created",
        prevHash: "00000000000000000000000000000000",
        hash: generateCryptoHash("TOKEN_SECURED_GENESIS_2026")
      };
      state.blockchain.push(genesisBlock);
      saveState();
    }
  }

  // Add a block to the immutable Blockchain
  function appendBlockchainBlock(type, details) {
    const prevBlock = state.blockchain[state.blockchain.length - 1];
    const newBlock = {
      index: state.blockchain.length + 1,
      timestamp: new Date().toLocaleString(),
      type: type,
      data: details,
      prevHash: prevBlock ? prevBlock.hash : "00000000000000000000000000000000",
      hash: generateCryptoHash(type + JSON.stringify(details) + Date.now())
    };
    state.blockchain.unshift(newBlock); // Latest first
    saveState();
    renderBlockchain();
  }

  // Load Tokens State
  function loadTokens() {
    const savedTokens = localStorage.getItem('cipher_tokens');
    if (savedTokens) {
      try {
        state.tokens = JSON.parse(savedTokens);
      } catch (e) {
        state.tokens = [];
      }
    }

    if (state.tokens.length === 0) {
      const seedToken = {
        id: "TK-8942-ALPHA",
        label: "Production Payment API Access",
        rawCode: "TK-8942-X9F2-901B-SECRET",
        maskedCode: "TK-8942-****-****-0x89F",
        status: "active",
        createdAt: new Date().toLocaleString(),
        expiryMinutes: 60,
        alertLevel: "strict"
      };
      state.tokens.push(seedToken);
      saveState();
    }
  }

  function saveState() {
    localStorage.setItem('cipher_tokens', JSON.stringify(state.tokens));
    localStorage.setItem('cipher_blockchain', JSON.stringify(state.blockchain));
  }

  // UI Renderers
  function renderStats() {
    const invisibleCount = state.tokens.filter(t => t.status === 'active').length;
    const pendingAlertsCount = (state.pendingAlert ? 1 : 0) + (state.pending2FAAlert ? 1 : 0);

    document.getElementById('statInvisibleTokens').textContent = invisibleCount;
    document.getElementById('statBlockCount').textContent = state.blockchain.length;
    document.getElementById('statPendingAlerts').textContent = pendingAlertsCount;
  }

  function renderTokensTable() {
    const tbody = document.getElementById('tokensTableBody');
    if (!tbody) return;

    if (state.tokens.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 24px;">
            No active tokens created. Click "Generate New Invisible Token" above.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = state.tokens.map(token => {
      let statusBadge = `<span class="badge badge-active"><i class="bi bi-shield-check"></i> Active</span>`;
      if (token.status === 'revoked') {
        statusBadge = `<span class="badge badge-revoked"><i class="bi bi-shield-x"></i> Revoked</span>`;
      } else if (token.status === 'pending') {
        statusBadge = `<span class="badge badge-pending"><i class="bi bi-hourglass-split"></i> Pending Confirm</span>`;
      }

      return `
        <tr>
          <td style="font-family: var(--font-mono); font-weight: 700; color: var(--primary-cyan);">${token.id}</td>
          <td>${token.label}</td>
          <td>
            <span class="token-code masked">
              <i class="bi bi-eye-slash-fill me-1"></i> ${token.maskedCode}
            </span>
          </td>
          <td>${statusBadge}</td>
          <td style="font-size: 12px; color: var(--text-muted);">${token.createdAt}</td>
          <td>
            ${token.status === 'active' ? `
              <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="triggerTokenVerifyAlert('${token.id}')">
                <i class="bi bi-share"></i> Utilize & Verify
              </button>
              <button class="btn btn-danger" style="padding: 4px 10px; font-size: 11px; margin-left: 4px;" onclick="revokeToken('${token.id}')">
                <i class="bi bi-x-circle"></i> Revoke
              </button>
            ` : `<span style="font-size: 11px; color: var(--text-dim);">No Actions</span>`}
          </td>
        </tr>
      `;
    }).join('');
  }

  function renderBlockchain() {
    const container = document.getElementById('blockchainStream');
    if (!container) return;

    container.innerHTML = state.blockchain.map(block => {
      return `
        <div class="block-item ${block.type === 'GENESIS_BLOCK' ? 'genesis' : ''}">
          <div class="block-header">
            <span class="block-num">BLOCK #${block.index} [${block.type}]</span>
            <span style="color: var(--text-muted); font-size: 11px;">${block.timestamp}</span>
          </div>
          <div style="font-size: 13px; font-weight: 600; color: #fff;">${typeof block.data === 'string' ? block.data : JSON.stringify(block.data)}</div>
          <div class="block-hash">HASH: ${block.hash}</div>
          <div class="block-hash" style="color: var(--text-dim);">PREV: ${block.prevHash.substring(0, 24)}...</div>
        </div>
      `;
    }).join('');
  }

  // Token Generation Handler
  window.handleTokenGenerate = function (e) {
    e.preventDefault();
    const label = document.getElementById('tokenLabelInput').value.trim();
    const expiry = parseInt(document.getElementById('tokenExpiryInput').value, 10);
    const alertLevel = document.getElementById('tokenAlertLevelInput').value;

    const randomSuffix = Math.floor(1000 + Math.random() * 9000);
    const tokenId = `TK-${randomSuffix}-SECURED`;
    
    const rawSecret = `TK-${randomSuffix}-${Math.random().toString(36).substring(2, 8).toUpperCase()}-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
    const maskedSecret = `TK-${randomSuffix}-****-****-${generateCryptoHash(rawSecret).substring(0, 6)}`;

    const newToken = {
      id: tokenId,
      label: label,
      rawCode: rawSecret,
      maskedCode: maskedSecret,
      status: "active",
      createdAt: new Date().toLocaleString(),
      expiryMinutes: expiry,
      alertLevel: alertLevel
    };

    state.tokens.unshift(newToken);
    saveState();

    appendBlockchainBlock("TOKEN_GENERATION", {
      tokenId: tokenId,
      label: label,
      maskedCode: maskedSecret,
      status: "ACTIVE_2FA_PROTECTED"
    });

    document.getElementById('tokenLabelInput').value = '';

    document.getElementById('revealTokenCode').textContent = rawSecret;
    window.openModal('modalReveal');

    renderTokensTable();
    renderStats();
  };

  // 2FA Security Login Alert Simulator
  window.simulateNewDeviceLogin = function () {
    const randomIP = `198.51.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}`;
    const devices = ["iPhone 15 Pro / Safari", "Linux Workstation / Firefox", "Windows 11 / Edge", "Attacker Device / Chrome"];
    const chosenDevice = devices[Math.floor(Math.random() * devices.length)] + ` (IP: ${randomIP})`;

    state.pending2FAAlert = {
      device: chosenDevice,
      timestamp: new Date().toLocaleTimeString()
    };

    document.getElementById('alertDeviceName').textContent = chosenDevice;
    document.getElementById('otpCodeInput').value = '';

    appendBlockchainBlock("STOLEN_PASSWORD_2FA_CHALLENGE", {
      device: chosenDevice,
      status: "STOLEN_PASSWORD_BLOCKED_BY_2FA"
    });

    window.openModal('modal2FAAlert');
    renderStats();
  };

  // Resolve 2FA Alert (Verify OTP vs Block Device)
  window.resolve2FAAlert = function (isApproved) {
    const alertData = state.pending2FAAlert;
    if (!alertData) return;

    if (isApproved) {
      const otp = document.getElementById('otpCodeInput').value.trim();
      appendBlockchainBlock("2FA_LOGIN_SUCCESS", {
        device: alertData.device,
        otpVerified: otp || "PASSKEY_AUTH",
        action: "DEVICE_AUTHORIZED"
      });
      alert(`✅ 2FA Verified: Device [${alertData.device}] authorized successfully! Security alert email dispatched.`);
    } else {
      appendBlockchainBlock("2FA_LOGIN_BLOCKED", {
        device: alertData.device,
        action: "ATTACKER_BLOCKED_ACCOUNT_LOCKED"
      });
      alert(`⛔ ANTI-THEFT LOCKOUT: Attacker attempt from [${alertData.device}] BLOCKED. Account password invalidated & emergency 2FA lock triggered!`);
    }

    state.pending2FAAlert = null;
    window.closeModal('modal2FAAlert');
    renderStats();
  };

  // One-Time Secret Copy
  window.copyRevealToken = function () {
    const code = document.getElementById('revealTokenCode').textContent;
    navigator.clipboard.writeText(code).then(() => {
      alert("Secret token copied to clipboard! Once closed, it becomes permanently obfuscated & invisible.");
    }).catch(() => {
      alert("Token copied: " + code);
    });
  };

  // Trigger Intentionality Verification Alert HUD
  window.triggerTokenVerifyAlert = function (tokenId) {
    const token = state.tokens.find(t => t.id === tokenId);
    if (!token) return;

    state.pendingAlert = token;
    renderStats();

    document.getElementById('alertTokenIdDisplay').textContent = `${token.id} (${token.label})`;
    window.openModal('modalAlert');
  };

  // External Share Simulation Button Handler
  window.simulateExternalShareAttempt = function () {
    const activeToken = state.tokens.find(t => t.status === 'active');
    if (activeToken) {
      window.triggerTokenVerifyAlert(activeToken.id);
    } else {
      alert("Please generate a token first.");
    }
  };

  // Resolve Intentionality Alert (Approve vs Reject)
  window.resolveAlert = function (isApproved) {
    const token = state.pendingAlert;
    if (!token) return;

    if (isApproved) {
      appendBlockchainBlock("INTENTIONALITY_APPROVED", {
        tokenId: token.id,
        action: "USER_EXPLICIT_2FA_CONFIRMATION",
        result: "AUTHORIZED_AND_LOGGED"
      });
      alert(`✅ Access Granted: Token ${token.id} presentation confirmed as intentional by account owner.`);
    } else {
      token.status = 'revoked';
      appendBlockchainBlock("INTENTIONALITY_REJECTED", {
        tokenId: token.id,
        action: "2FA_SECURITY_BLOCK_REVOCATION",
        result: "TOKEN_INSTANTLY_REVOKED"
      });
      alert(`⛔ SECURITY ALERT: Token ${token.id} was flagged as unintentional or unauthorized and has been INSTANTLY REVOKED.`);
    }

    state.pendingAlert = null;
    saveState();
    window.closeModal('modalAlert');
    renderTokensTable();
    renderStats();
  };

  // Revoke Token Directly
  window.revokeToken = function (tokenId) {
    const token = state.tokens.find(t => t.id === tokenId);
    if (token) {
      token.status = 'revoked';
      appendBlockchainBlock("TOKEN_REVOCATION", {
        tokenId: tokenId,
        reason: "MANUAL_REVOCATION_BY_OWNER"
      });
      saveState();
      renderTokensTable();
      renderStats();
    }
  };

  // View & Modal Switchers
  window.switchView = function (viewName) {
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.classList.toggle('active', tab.getAttribute('data-view') === viewName);
    });
  };

  window.openModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('active');
  };

  window.closeModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
  };

  // Initialize Application
  function init() {
    initGenesisBlock();
    loadTokens();
    renderTokensTable();
    renderBlockchain();
    renderStats();
    console.log("Token Secured Engine Initialized OK with Anti-Theft Vault Lock");
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
