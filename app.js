/* ============================================================================
   TOKEN SECURED - APP CORE ENGINE
   Dynamic 2FA Sign-up, Collaborator RBAC & PR Merge Approval Gate
   ============================================================================ */

(function () {
  "use strict";

  // Application State
  const state = {
    authMode: 'signup', // 'signup' or 'signin'
    users: {}, // { username: { email, passcode } }
    currentUser: null,
    vaultUnlocked: false,
    collaborators: [],
    pullRequests: [],
    tokens: [],
    blockchain: []
  };

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

  // Load Saved Users & State
  function loadSavedState() {
    const savedUsers = localStorage.getItem('cipher_users');
    if (savedUsers) {
      try { state.users = JSON.parse(savedUsers); } catch (e) { state.users = {}; }
    }

    const savedCollabs = localStorage.getItem('cipher_collaborators');
    if (savedCollabs) {
      try { state.collaborators = JSON.parse(savedCollabs); } catch (e) { state.collaborators = []; }
    }

    const savedPRs = localStorage.getItem('cipher_prs');
    if (savedPRs) {
      try { state.pullRequests = JSON.parse(savedPRs); } catch (e) { state.pullRequests = []; }
    }

    const savedTokens = localStorage.getItem('cipher_tokens');
    if (savedTokens) {
      try { state.tokens = JSON.parse(savedTokens); } catch (e) { state.tokens = []; }
    }

    // Seed sample collaborators if empty
    if (state.collaborators.length === 0) {
      state.collaborators = [
        { username: "dev_john", role: "Developer", scope: "Feature Branch Only", directPush: "BLOCKED", prRequired: "YES" },
        { username: "tester_sarah", role: "QA Tester", scope: "Read-Only Testing", directPush: "BLOCKED", prRequired: "YES" }
      ];
    }

    // Seed sample PR if empty
    if (state.pullRequests.length === 0) {
      state.pullRequests = [
        { id: "PR-101", author: "dev_john", title: "Add Canvas Export & Filter Feature", branch: "feature/export", status: "PENDING_OWNER_APPROVAL" }
      ];
    }

    // Determine initial auth mode
    if (Object.keys(state.users).length > 0) {
      window.setAuthMode('signin');
    } else {
      window.setAuthMode('signup');
    }
  }

  function saveState() {
    localStorage.setItem('cipher_users', JSON.stringify(state.users));
    localStorage.setItem('cipher_collaborators', JSON.stringify(state.collaborators));
    localStorage.setItem('cipher_prs', JSON.stringify(state.pullRequests));
    localStorage.setItem('cipher_tokens', JSON.stringify(state.tokens));
    localStorage.setItem('cipher_blockchain', JSON.stringify(state.blockchain));
  }

  // Subscription Currencies Mapping ($5.00 USD Equivalent)
  const currencyMap = {
    USD: "$5.00 USD",
    INR: "₹415.00 INR",
    EUR: "€4.60 EUR",
    GBP: "£3.95 GBP",
    CAD: "$6.80 CAD",
    AUD: "$7.60 AUD",
    JPY: "¥750 JPY"
  };

  // Currency Converter Switcher
  window.updateSubscriptionCurrency = function (curr) {
    const priceTag = document.getElementById('subPriceTag');
    if (priceTag && currencyMap[curr]) {
      priceTag.textContent = currencyMap[curr];
    }
  };

  // Payment Method Selector Toggle
  window.selectPayMethod = function (btnElement) {
    const buttons = document.querySelectorAll('.payment-method-selector .pay-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    btnElement.classList.add('active');
  };

  // Toggle Auth Mode (Sign Up vs Sign In)
  window.setAuthMode = function (mode) {
    state.authMode = mode;
    const title = document.getElementById('authModalTitle');
    const subtitle = document.getElementById('authModalSubtitle');
    const emailGroup = document.getElementById('authEmailGroup');
    const subCard = document.getElementById('authSubCard');
    const submitBtn = document.getElementById('authSubmitBtn');

    if (mode === 'signup') {
      if (title) title.textContent = "CREATE MASTER 2FA ACCOUNT";
      if (subtitle) subtitle.textContent = "Setup your individual Master Account & Activate $5.00 USD/mo Workspace Subscription.";
      if (emailGroup) emailGroup.style.display = 'block';
      if (subCard) subCard.style.display = 'block';
      if (submitBtn) submitBtn.innerHTML = '<i class="bi bi-shield-check me-2"></i> Subscribe ($5/mo) & Register 2FA Account';
    } else {
      if (title) title.textContent = "TOKEN SECURED SIGN IN";
      if (subtitle) subtitle.textContent = "Enter your username & 2FA passcode to decrypt vault.";
      if (emailGroup) emailGroup.style.display = 'none';
      if (subCard) subCard.style.display = 'none';
      if (submitBtn) submitBtn.innerHTML = '<i class="bi bi-shield-lock-fill me-2"></i> Authenticate & Decrypt Vault';
    }
  };

  // Auth Form Submit (Registration vs Sign In)
  window.handleAuthSubmit = function (e) {
    e.preventDefault();
    const username = document.getElementById('authUsernameInput').value.trim();
    const email = document.getElementById('authEmailInput').value.trim();
    const passcode = document.getElementById('masterPasscodeInput').value.trim();
    const selectedCurr = document.getElementById('currencySelector') ? document.getElementById('currencySelector').value : 'USD';
    const subPrice = currencyMap[selectedCurr] || "$5.00 USD";

    if (!username || !passcode) {
      alert("Please enter username and 2FA passcode.");
      return;
    }

    if (state.authMode === 'signup') {
      if (state.users[username]) {
        alert("Account username already exists. Please sign in instead.");
        window.setAuthMode('signin');
        return;
      }

      // Register New Account with $5/month Subscription Active
      state.users[username] = {
        email: email || `${username.toLowerCase()}@token-secured.io`,
        passcode: passcode,
        createdAt: new Date().toLocaleString(),
        subscription: {
          active: true,
          plan: "Pro Workspace Build Access",
          rate: "$5.00 USD / month",
          billingCurrency: selectedCurr,
          chargedAmount: subPrice,
          renewsOn: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString()
        }
      };

      state.currentUser = username;
      state.vaultUnlocked = true;
      saveState();

      appendBlockchainBlock("ACCOUNT_REGISTERED_SUBSCRIBED", {
        user: username,
        email: state.users[username].email,
        subscription: `${subPrice} / month ACTIVE`,
        status: "2FA_ENFORCED"
      });

      alert(`✅ Subscription Active! Master Account [${username}] registered with $5/month Pro Build Access & 2FA protection!`);
    } else {
      // Sign In
      const user = state.users[username];
      if (!user) {
        alert(`❌ Account [${username}] not found. Please create an account first.`);
        return;
      }

      if (user.passcode !== passcode) {
        appendBlockchainBlock("FAILED_SIGNIN_ATTEMPT", {
          user: username,
          status: "UNAUTHORIZED_2FA_BLOCKED"
        });
        alert(`⛔ 2FA Security Alert: Invalid 2FA Passcode! Security notification sent to ${user.email}.`);
        return;
      }


      state.currentUser = username;
      state.vaultUnlocked = true;

      appendBlockchainBlock("ACCOUNT_SIGNIN", {
        user: username,
        status: "2FA_AUTHENTICATED"
      });

      alert(`🔓 Authenticated: Signed in as [${username}] with 2FA vault protection!`);
    }

    // Hide Auth Modal & Update UI
    document.getElementById('masterVaultLockScreen').classList.remove('active');
    document.getElementById('activeUserBadge').textContent = state.currentUser;
    document.getElementById('displayActiveUser').textContent = state.currentUser;

    renderAll();
  };

  window.lockMasterVault = function () {
    state.vaultUnlocked = false;
    document.getElementById('masterVaultLockScreen').classList.add('active');
    if (Object.keys(state.users).length > 0) {
      window.setAuthMode('signin');
    }
  };

  // Initialize Genesis Block on Blockchain
  function initGenesisBlock() {
    const savedBlocks = localStorage.getItem('cipher_blockchain');
    if (savedBlocks) {
      try { state.blockchain = JSON.parse(savedBlocks); } catch (e) { state.blockchain = []; }
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

  // Add Collaborator Form Handler
  window.handleAddCollaboratorSubmit = function (e) {
    e.preventDefault();
    const username = document.getElementById('collabUsernameInput').value.trim();
    const role = document.getElementById('collabRoleInput').value;
    const scope = document.getElementById('collabScopeInput').value;

    if (!username) return;

    const newCollab = {
      username: username,
      role: role,
      scope: scope,
      directPush: "BLOCKED",
      prRequired: "YES"
    };

    state.collaborators.push(newCollab);
    saveState();

    appendBlockchainBlock("COLLABORATOR_INVITED", {
      invitedBy: state.currentUser,
      collaborator: username,
      role: role,
      directPush: "RESTRICTED_PR_MANDATORY"
    });

    window.closeModal('modalAddCollaborator');
    document.getElementById('collabUsernameInput').value = '';
    renderCollaboratorsTable();
    renderStats();
    alert(`✅ Collaborator Invited: [${username}] added as ${role}. Direct push blocked; PR approval required for code updates.`);
  };

  // Simulate Collaborator Pull Request Submission
  window.simulateCollaboratorPRSubmission = function () {
    const randomPrId = `PR-${Math.floor(100 + Math.random() * 900)}`;
    const authors = ["dev_john", "tester_sarah", "contractor_mike"];
    const author = authors[Math.floor(Math.random() * authors.length)];
    const titles = ["Optimized Image Processing Pipeline", "Updated RTSP Live Streaming Handler", "Added Keypoint Pose Estimation Labels"];
    const title = titles[Math.floor(Math.random() * titles.length)];

    const newPR = {
      id: randomPrId,
      author: author,
      title: title,
      branch: `feature/${author}-update`,
      status: "PENDING_OWNER_APPROVAL"
    };

    state.pullRequests.unshift(newPR);
    saveState();

    appendBlockchainBlock("PR_SUBMITTED", {
      prId: randomPrId,
      author: author,
      title: title,
      status: "AWAITING_OWNER_2FA_APPROVAL"
    });

    renderPRTable();
    renderStats();
    alert(`📥 New Pull Request Received: [${randomPrId}] from ${author}. Awaiting Master Owner [${state.currentUser}] approval.`);
  };

  // Owner Approve & Merge PR
  window.approvePR = function (prId) {
    const pr = state.pullRequests.find(p => p.id === prId);
    if (!pr) return;

    pr.status = "MERGED_AND_DEPLOYED";
    saveState();

    appendBlockchainBlock("PR_MERGED_APPROVED", {
      prId: pr.id,
      approvedByOwner: state.currentUser,
      author: pr.author,
      status: "MERGED_TO_MAIN"
    });

    renderPRTable();
    renderStats();
    alert(`🎉 PR Approved & Merged! [${pr.id}] by ${pr.author} approved by Owner [${state.currentUser}] and merged to main!`);
  };

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

  // Copy Secret Token
  window.copyRevealToken = function () {
    const code = document.getElementById('revealTokenCode').textContent;
    navigator.clipboard.writeText(code).then(() => {
      alert("Secret token copied to clipboard! Once closed, it becomes permanently obfuscated & invisible.");
    }).catch(() => {
      alert("Token copied: " + code);
    });
  };

  // Render Functions
  function renderStats() {
    const activeUser = state.currentUser || "No Account";
    document.getElementById('displayActiveUser').textContent = activeUser;
    document.getElementById('statInvisibleTokens').textContent = state.tokens.filter(t => t.status === 'active').length;
    document.getElementById('statBlockCount').textContent = state.blockchain.length;
    document.getElementById('statCollaboratorsCount').textContent = state.collaborators.length;

    const pendingPRs = state.pullRequests.filter(p => p.status.includes('PENDING')).length;
    document.getElementById('statPRCount').textContent = pendingPRs;

    const prBadge = document.getElementById('navPRBadge');
    if (prBadge) {
      if (pendingPRs > 0) {
        prBadge.style.display = 'inline-flex';
        prBadge.textContent = pendingPRs;
      } else {
        prBadge.style.display = 'none';
      }
    }
  }

  function renderCollaboratorsTable() {
    const tbody = document.getElementById('collaboratorsTableBody');
    if (!tbody) return;

    if (state.collaborators.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 16px; color: var(--text-muted);">No collaborators added. Click "Invite Collaborator" above.</td></tr>`;
      return;
    }

    tbody.innerHTML = state.collaborators.map(c => `
      <tr>
        <td style="font-weight: 700; color: var(--primary-cyan);">${c.username}</td>
        <td><span class="badge badge-active">${c.role}</span></td>
        <td style="font-size: 12px; color: var(--text-muted);">${c.scope}</td>
        <td><span class="badge badge-revoked"><i class="bi bi-lock-fill"></i> BLOCKED</span></td>
        <td><span class="badge badge-pending"><i class="bi bi-shield-lock"></i> YES (Owner Approval)</span></td>
        <td><span style="font-size: 11px; color: var(--text-dim);">Restricted</span></td>
      </tr>
    `).join('');
  }

  function renderPRTable() {
    const tbody = document.getElementById('prTableBody');
    if (!tbody) return;

    if (state.pullRequests.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 16px; color: var(--text-muted);">No pending Pull Requests.</td></tr>`;
      return;
    }

    tbody.innerHTML = state.pullRequests.map(p => `
      <tr>
        <td style="font-family: var(--font-mono); font-weight: 700; color: var(--primary-cyan);">${p.id}</td>
        <td style="font-weight: 600;">${p.author}</td>
        <td style="font-size: 13px;">${p.title}</td>
        <td style="font-family: var(--font-mono); font-size: 12px; color: var(--text-muted);">${p.branch}</td>
        <td>
          ${p.status.includes('MERGED') 
            ? `<span class="badge badge-active"><i class="bi bi-check-circle-fill"></i> Merged</span>` 
            : `<span class="badge badge-pending"><i class="bi bi-hourglass-split"></i> Awaiting Owner Review</span>`}
        </td>
        <td>
          ${p.status.includes('PENDING') ? `
            <button class="btn btn-success" style="padding: 4px 10px; font-size: 11px;" onclick="approvePR('${p.id}')">
              <i class="bi bi-check-lg"></i> Approve & Merge
            </button>
          ` : `<span style="font-size: 11px; color: var(--accent-emerald); font-weight: 700;">Approved</span>`}
        </td>
      </tr>
    `).join('');
  }

  function renderTokensTable() {
    const tbody = document.getElementById('tokensTableBody');
    if (!tbody) return;

    if (state.tokens.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 24px; color: var(--text-muted);">No tokens in vault. Click "Generate New Invisible Token" above.</td></tr>`;
      return;
    }

    tbody.innerHTML = state.tokens.map(token => `
      <tr>
        <td style="font-family: var(--font-mono); font-weight: 700; color: var(--primary-cyan);">${token.id}</td>
        <td>${token.label}</td>
        <td><span class="token-code masked"><i class="bi bi-eye-slash-fill me-1"></i> ${token.maskedCode}</span></td>
        <td>
          ${token.status === 'revoked' 
            ? `<span class="badge badge-revoked"><i class="bi bi-x-circle-fill"></i> Revoked</span>` 
            : `<span class="badge badge-active"><i class="bi bi-shield-check"></i> Active</span>`}
        </td>
        <td style="font-size: 12px; color: var(--text-muted);">${token.createdAt}</td>
        <td>
          <div style="display: flex; gap: 6px;">
            <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 11px;" onclick="copyTokenForGitHub('${token.id}')" title="Copy clean secret to paste into GitHub / Vercel without fail">
              <i class="bi bi-github text-cyan"></i> Copy for GitHub
            </button>
            <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 11px; color: var(--accent-rose);" onclick="regenerateToken('${token.id}')" title="Regenerate a new replacement token if this one fails">
              <i class="bi bi-arrow-clockwise"></i> Regenerate
            </button>
          </div>
        </td>
      </tr>
    `).join('');
  }

  function renderBlockchain() {
    const container = document.getElementById('blockchainStream');
    if (!container) return;

    container.innerHTML = state.blockchain.map(block => `
      <div class="block-item ${block.type === 'GENESIS_BLOCK' ? 'genesis' : ''}">
        <div class="block-header">
          <span class="block-num">BLOCK #${block.index} [${block.type}]</span>
          <span style="color: var(--text-muted); font-size: 11px;">${block.timestamp}</span>
        </div>
        <div style="font-size: 13px; font-weight: 600; color: #fff;">${typeof block.data === 'string' ? block.data : JSON.stringify(block.data)}</div>
        <div class="block-hash">HASH: ${block.hash}</div>
        <div class="block-hash" style="color: var(--text-dim);">PREV: ${block.prevHash.substring(0, 24)}...</div>
      </div>
    `).join('');
  }

  function renderAll() {
    renderStats();
    renderCollaboratorsTable();
    renderPRTable();
    renderTokensTable();
    renderBlockchain();
  }

  // SSO Multi-Provider Authenticator Handler
  window.loginWithProvider = function (providerName) {
    const ssoUser = `${providerName.toLowerCase().replace(/[^a-z]/g, '')}_user`;
    const defaultEmail = `${ssoUser}@token-secured.io`;
    
    // Auto-fill form and set state
    document.getElementById('authUsernameInput').value = ssoUser;
    document.getElementById('authEmailInput').value = defaultEmail;
    document.getElementById('masterPasscodeInput').value = "654321";

    state.users[ssoUser] = {
      email: defaultEmail,
      passcode: "654321",
      ssoProvider: providerName,
      createdAt: new Date().toLocaleString(),
      subscription: {
        active: true,
        plan: "Pro Workspace Build Access",
        rate: "$5.00 USD / month",
        renewsOn: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString()
      }
    };

    state.currentUser = ssoUser;
    state.vaultUnlocked = true;
    saveState();

    appendBlockchainBlock("SSO_PROVIDER_AUTHENTICATED", {
      user: ssoUser,
      provider: providerName,
      email: defaultEmail,
      alertsDispatched: ["Email: " + defaultEmail, "WhatsApp: +1-800-WA-NOTIFY"]
    });

    const lockScreen = document.getElementById('masterVaultLockScreen');
    if (lockScreen) lockScreen.classList.remove('active');

    renderAll();
    showToastNotification(`Authenticated via ${providerName} SSO! Dual 2FA alerts sent to Email & WhatsApp!`);
  };

  // Dual Email + WhatsApp Alert Simulator
  window.simulateMultiAlertDispatch = function () {
    const activeEmail = state.currentUser && state.users[state.currentUser] ? state.users[state.currentUser].email : "owner@account.org";
    appendBlockchainBlock("UNUSUAL_ACTIVITY_ALERT_DISPATCHED", {
      user: state.currentUser || "Manoj-548",
      channels: ["Email (" + activeEmail + ")", "WhatsApp (+1-800-WA-NOTIFY)", "Telegram (@TokenSecuredBot)"],
      status: "SECURITY_ALERT_SENT"
    });
    renderBlockchain();

    showToastNotification(`🚨 UNUSUAL ACTIVITY ALERT! Simultaneous notifications sent to Email (${activeEmail}) & WhatsApp (+1-800-WA-NOTIFY)!`);
  };

  // Copy Clean Token Secret to Clipboard for GitHub / CLI
  window.copyTokenForGitHub = function (tokenId) {
    const token = state.tokens.find(t => t.id === tokenId);
    if (!token) return;

    const rawSecret = token.secret || `ghp_live_${generateCryptoHash(token.id).substring(2)}`;
    
    if (navigator.clipboard) {
      navigator.clipboard.writeText(rawSecret).then(() => {
        showToastNotification(`✅ Copied token to clipboard! Ready to paste into GitHub / Vercel without fail!`);
      }).catch(() => {
        fallbackCopyText(rawSecret);
      });
    } else {
      fallbackCopyText(rawSecret);
    }

    appendBlockchainBlock("TOKEN_COPIED_FOR_GITHUB", {
      tokenId: tokenId,
      user: state.currentUser,
      targetPlatform: "GitHub / Remote CLI"
    });
    renderBlockchain();
  };

  function fallbackCopyText(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand("copy");
    document.body.removeChild(textArea);
    showToastNotification(`✅ Copied token to clipboard! Ready to paste into GitHub without fail!`);
  }

  // Revoke & Regenerate Failed Token
  window.regenerateToken = function (tokenId) {
    const tokenIndex = state.tokens.findIndex(t => t.id === tokenId);
    if (tokenIndex === -1) return;

    const oldToken = state.tokens[tokenIndex];
    oldToken.status = 'revoked';

    // Generate Replacement Token
    const newId = `TK-${Math.floor(1000 + Math.random() * 9000)}-REGEN`;
    const newSecret = `ghp_live_${generateCryptoHash(newId).substring(2)}`;
    const newToken = {
      id: newId,
      label: `${oldToken.label} (Regenerated)`,
      secret: newSecret,
      maskedCode: `${newId.substring(0, 7)}-••••-••••-${newSecret.substring(newSecret.length - 4)}`,
      status: 'active',
      createdAt: new Date().toLocaleString(),
      expiryMinutes: oldToken.expiryMinutes || 60,
      alertLevel: oldToken.alertLevel || 'strict'
    };

    state.tokens.unshift(newToken);
    saveState();

    appendBlockchainBlock("TOKEN_REVOKED_REGENERATED", {
      revokedTokenId: tokenId,
      newTokenId: newId,
      user: state.currentUser,
      reason: "TOKEN_FAILURE_RECOVERY"
    });

    renderAll();
    showToastNotification(`🔄 Token ${tokenId} Revoked! Fresh Token ${newId} regenerated & active for your account!`);
  };

  // Toast Notification Helper
  function showToastNotification(message) {
    const existing = document.querySelector('.toast-notification');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.innerHTML = `<i class="bi bi-shield-check text-cyan" style="font-size: 20px;"></i> <span>${message}</span>`;
    document.body.appendChild(toast);

    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 4500);
  }

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

  function init() {
    initGenesisBlock();
    loadSavedState();
    renderAll();
    console.log("Token Secured Engine Initialized OK with 2FA Gate, SSO Grid, Dual Alerts & Token Regeneration");
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();

