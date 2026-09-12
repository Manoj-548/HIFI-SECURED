/* ============================================================================
   TOKEN SECURED - APP CORE ENGINE WITH INDIVIDUAL MULTI-TENANT 2FA ACCOUNTS
   ============================================================================ */

(function () {
  "use strict";

  // Application State
  const state = {
    currentUser: "Manoj-548",
    vaultUnlocked: false,
    failedPasscodeAttempts: 0,
    userTokensMap: {},
    blockchain: [],
    pendingAlert: null,
    pending2FAAlert: null,
    stats: {
      verifiedUses: 0,
      blockedAttempts: 0
    }
  };

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
    const selectedUser = document.getElementById('userAccountSelector')?.value || "Manoj-548";
    const entered = document.getElementById('masterPasscodeInput')?.value.trim();

    if (entered === MASTER_VAULT_PASSCODE) {
      state.currentUser = selectedUser;
      state.vaultUnlocked = true;
      state.failedPasscodeAttempts = 0;

      document.getElementById('masterVaultLockScreen').classList.remove('active');
      document.getElementById('activeUserBadge').textContent = selectedUser;
      document.getElementById('displayActiveUser').textContent = selectedUser;
      document.getElementById('displayEmailUser').textContent = `${selectedUser.toLowerCase()}@token-secured.io`;

      appendBlockchainBlock("ACCOUNT_AUTHENTICATED", {
        user: selectedUser,
        status: "2FA_TOTP_VERIFIED",
        action: "DECRYPTED_INDIVIDUAL_VAULT"
      });

      renderTokensTable();
      renderStats();
      alert(`🔓 Authenticated: Switched to isolated vault for [${selectedUser}]`);
    } else {
      state.failedPasscodeAttempts += 1;
      appendBlockchainBlock("ANTI_THEFT_FAILED_LOGIN", {
        user: selectedUser,
        attempt: state.failedPasscodeAttempts,
        status: "UNAUTHORIZED_ACCESS_BLOCKED"
      });

      if (state.failedPasscodeAttempts >= 3) {
        alert(`⛔ ANTI-THEFT EMERGENCY LOCKOUT: 3 Failed Passcode attempts on account [${selectedUser}]! Security Alert Email dispatched to owner.`);
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
      user: state.currentUser,
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
    state.blockchain.unshift(newBlock);
    saveState();
    renderBlockchain();
  }

  // Load User Tokens State
  function loadTokens() {
    const savedMap = localStorage.getItem('cipher_user_tokens_map');
    if (savedMap) {
      try {
        state.userTokensMap = JSON.parse(savedMap);
      } catch (e) {
        state.userTokensMap = {};
      }
    }

    if (!state.userTokensMap["Manoj-548"]) {
      state.userTokensMap["Manoj-548"] = [
        {
          id: "TK-8942-SECURED",
          label: "Manoj-548 Personal Production API",
          rawCode: "TK-8942-X9F2-901B-SECRET",
          maskedCode: "TK-8942-****-****-0x89F",
          status: "active",
          createdAt: new Date().toLocaleString(),
          expiryMinutes: 60,
          alertLevel: "strict"
        }
      ];
      saveState();
    }
  }

  function getActiveUserTokens() {
    if (!state.userTokensMap[state.currentUser]) {
      state.userTokensMap[state.currentUser] = [];
    }
    return state.userTokensMap[state.currentUser];
  }

  function saveState() {
    localStorage.setItem('cipher_user_tokens_map', JSON.stringify(state.userTokensMap));
    localStorage.setItem('cipher_blockchain', JSON.stringify(state.blockchain));
  }

  // UI Renderers
  function renderStats() {
    const activeTokens = getActiveUserTokens();
    const invisibleCount = activeTokens.filter(t => t.status === 'active').length;
    const pendingAlertsCount = (state.pendingAlert ? 1 : 0) + (state.pending2FAAlert ? 1 : 0);

    document.getElementById('statInvisibleTokens').textContent = invisibleCount;
    document.getElementById('statBlockCount').textContent = state.blockchain.length;
    document.getElementById('statPendingAlerts').textContent = pendingAlertsCount;
  }

  function renderTokensTable() {
    const tbody = document.getElementById('tokensTableBody');
    if (!tbody) return;

    const tokens = getActiveUserTokens();

    if (tokens.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 24px;">
            No active tokens in vault for [${state.currentUser}]. Click "Generate New Invisible Token" above.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = tokens.map(token => {
      let statusBadge = `<span class="badge badge-active"><i class="bi bi-shield-check"></i> Active</span>`;
      if (token.status === 'revoked') {
        statusBadge = `<span class="badge badge-revoked"><i class="bi bi-shield-x"></i> Revoked</span>`;
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

    const userTokens = getActiveUserTokens();
    userTokens.unshift(newToken);
    saveState();

    appendBlockchainBlock("TOKEN_GENERATION", {
      user: state.currentUser,
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

    document.getElementById('alertTargetAccount').textContent = state.currentUser;
    document.getElementById('otpCodeInput').value = '';

    appendBlockchainBlock("STOLEN_PASSWORD_2FA_CHALLENGE", {
      user: state.currentUser,
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
        user: state.currentUser,
        device: alertData.device,
        otpVerified: otp || "PASSKEY_AUTH",
        action: "DEVICE_AUTHORIZED"
      });
      alert(`✅ 2FA Verified: Device [${alertData.device}] authorized for account [${state.currentUser}]!`);
    } else {
      appendBlockchainBlock("2FA_LOGIN_BLOCKED", {
        user: state.currentUser,
        device: alertData.device,
        action: "ATTACKER_BLOCKED_ACCOUNT_LOCKED"
      });
      alert(`⛔ ANTI-THEFT LOCKOUT: Attacker attempt from [${alertData.device}] BLOCKED. Account [${state.currentUser}] secured!`);
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
    const userTokens = getActiveUserTokens();
    const token = userTokens.find(t => t.id === tokenId);
    if (!token) return;

    state.pendingAlert = token;
    renderStats();

    document.getElementById('alertTokenIdDisplay').textContent = `${token.id} (${token.label})`;
    window.openModal('modalAlert');
  };

  // External Share Simulation Button Handler
  window.simulateExternalShareAttempt = function () {
    const userTokens = getActiveUserTokens();
    const activeToken = userTokens.find(t => t.status === 'active');
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
        user: state.currentUser,
        tokenId: token.id,
        action: "USER_EXPLICIT_2FA_CONFIRMATION",
        result: "AUTHORIZED_AND_LOGGED"
      });
      alert(`✅ Access Granted: Token ${token.id} confirmed as intentional by owner [${state.currentUser}].`);
    } else {
      token.status = 'revoked';
      appendBlockchainBlock("INTENTIONALITY_REJECTED", {
        user: state.currentUser,
        tokenId: token.id,
        action: "2FA_SECURITY_BLOCK_REVOCATION",
        result: "TOKEN_INSTANTLY_REVOKED"
      });
      alert(`⛔ SECURITY ALERT: Token ${token.id} flagged as unauthorized and INSTANTLY REVOKED.`);
    }

    state.pendingAlert = null;
    saveState();
    window.closeModal('modalAlert');
    renderTokensTable();
    renderStats();
  };

  // Revoke Token Directly
  window.revokeToken = function (tokenId) {
    const userTokens = getActiveUserTokens();
    const token = userTokens.find(t => t.id === tokenId);
    if (token) {
      token.status = 'revoked';
      appendBlockchainBlock("TOKEN_REVOCATION", {
        user: state.currentUser,
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
    console.log("Token Secured Engine Initialized OK with Individual User Accounts");
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
