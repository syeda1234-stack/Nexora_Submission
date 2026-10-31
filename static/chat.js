(() => {
  function initNexoraChat() {
    const form=document.getElementById('chat-form'), input=document.getElementById('chat-input');
    const messages=document.getElementById('chat-messages'), status=document.getElementById('assistant-status');
    if(!form||!input||!messages||form.dataset.chatBound==='1') return;
    form.dataset.chatBound='1'; const button=form.querySelector('button[type="submit"]'); let busy=false; const sessionId=(window.crypto&&crypto.randomUUID?crypto.randomUUID():String(Date.now())+Math.random().toString(16).slice(2));
    const scroll=()=>{messages.scrollTop=messages.scrollHeight};
    function add(text,who){const el=document.createElement('div');el.className='message '+(who==='user'?'user-message':'assistant-message');el.textContent=text;messages.appendChild(el);scroll();return el;}

    const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    function renderAgent(el,data){
      const calls=Array.isArray(data.tool_calls)?data.tool_calls:[];
      if(calls.length||(data.plan&&data.plan.length)){
        const d=document.createElement('details');d.className='agent-trace';
        const via=data.mode==='ai'?((data.framework||'LangChain')+' · '+(data.provider||'LLM')):'Offline planner';
        d.innerHTML='<summary>Agent activity · '+calls.length+' tool call'+(calls.length===1?'':'s')+' · '+esc(via)+'</summary>'+
          '<ol class="agent-steps">'+(data.plan||[]).map(p=>'<li>'+esc(p)+'</li>').join('')+'</ol>'+
          calls.map(c=>'<div class="agent-tool"><b>'+esc(c.tool)+'</b> <span>'+(c.ok===false?'failed':esc(c.ms)+' ms')+'</span><code>'+esc(JSON.stringify(c.input))+'</code></div>').join('');
        el.appendChild(d);
      }
      const p=data.pending_confirmation;
      if(p&&p.intent_id){
        const card=document.createElement('div');card.className='confirm-card';
        card.innerHTML='<strong>Review sandbox transfer</strong><div>To: '+esc(p.recipient)+'</div><div>Send: '+esc(p.send)+' '+esc(p.base)+' (fee '+esc(p.fee)+')</div><div>Recipient gets ≈ '+esc(p.estimated_recipient_amount)+' '+esc(p.quote)+'</div><small>Simulation only. No money moves.</small>';
        const b=document.createElement('button');b.type='button';b.textContent='Confirm (simulated)';
        b.onclick=async()=>{b.disabled=true;try{const r=await fetch('/api/agent/transfer/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({intent_id:p.intent_id,confirm:true})});const j=await r.json();b.textContent=r.ok?'Confirmed · '+j.status:'Could not confirm';}catch(e){b.textContent='Could not confirm';b.disabled=false;}};
        card.appendChild(b);el.appendChild(card);
      }
      scroll();
    }
    function fit(){input.style.height='24px';input.style.height=Math.min(Math.max(input.scrollHeight,24),140)+'px';}
    function demoReply(q){const s=q.toLowerCase();if(s.includes('afford')||s.includes('budget')||s.includes('expense'))return 'Demo budget check: enter your monthly available funds and your tuition, housing, food, transport and other costs in the planner. Nexora can compare those estimates and show the remaining balance. This demo does not verify real prices.';if(s.includes('tuition')||s.includes('living'))return 'Demo tuition plan: separate tuition from monthly living costs, divide upcoming fees by the months remaining, and keep an emergency buffer. Confirm amounts and due dates with your university.';if(s.includes('convert')||s.includes('transfer')||s.includes('currency')||s.includes('remit'))return 'Before transferring money, compare the exchange rate, transfer fee, delivery time and amount the recipient will receive. Verify the final quote with the provider; this demo does not send money or fetch live rates.';return 'I’m Nexora in demo mode. I can help organize a student budget, plan tuition and living costs, and explain cross-border transfer checks. For a more specific estimate, enter your budget figures in the planner. No money is moved.';}
   
async function send(raw) {
  const q = String(raw || '').trim();
  if (!q || busy) return;

  add(q, 'user');
  input.value = '';
  fit();

  const pending = add('Thinking…', 'assistant');
  busy = true;
  input.disabled = true;
  if (button) button.disabled = true;
  if (status) status.textContent = 'Working…';

  try {
    const ids = ['currency', 'income', 'tuition', 'housing', 'food', 'transport', 'other'];
    const getField = id => document.getElementById(id);
    const n = id => Math.max(0, Number(getField(id)?.value || 0) || 0);

    const currency = getField('currency')?.value || 'BDT';
    const lower = q.toLowerCase();

const categories = [
  { keys: ['tuition', 'university fee'], id: 'tuition' },
  { keys: ['food', 'groceries'], id: 'food' },
  { keys: ['housing', 'rent', 'accommodation', 'living costs', 'living expenses'], id: 'housing' },
  { keys: ['transport', 'travel'], id: 'transport' },
  { keys: ['other expenses', 'other costs'], id: 'other' }
];

const parseAmount = text => {
  const match = text.match(/(?:৳|tk\.?\s*|bdt\s*)?([\d,]+(?:\.\d+)?)/i);
  return match ? Number(match[1].replace(/,/g, '')) : null;
};

const incomeMatch = lower.match(
  /(?:income|available funds|available|budget|have)\D{0,20}([\d,]+(?:\.\d+)?)/i
);

if (incomeMatch) {
  const income = Number(incomeMatch[1].replace(/,/g, ''));
  if (Number.isFinite(income) && income >= 0) {
    document.getElementById('income').value = income;
  }
}

for (const category of categories) {
  for (const key of category.keys) {
    const escapedKey = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const pattern = new RegExp(
      escapedKey + '\\s*(?:to|of|is|=|:)??\\s*(?:৳|tk\\.?\\s*|bdt\\s*)?([\\d,]+(?:\\.\\d+)?)',
      'i'
    );

    const match = q.match(pattern);

    if (match) {
      const amount = Number(match[1].replace(/,/g, ''));
      if (Number.isFinite(amount) && amount >= 0) {
        document.getElementById(category.id).value = amount;
      }
      break;
    }
  }
}

document.getElementById('budget-form')?.dispatchEvent(
  new Event('submit', { bubbles: true, cancelable: true })
);

    const context = {
      currency,
      income: n('income'),
      tuition: n('tuition'),
      housing: n('housing'),
      food: n('food'),
      transport: n('transport'),
      other: n('other')
    };

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: q, context, language: 'en', session_id: sessionId })
    });

    const data = await response.json();

    const reply = data && typeof data.reply === 'string' && data.reply.trim() ? data.reply : demoReply(q);
    pending.innerHTML = esc(reply)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');

    renderAgent(pending, data || {});
    if (status) {
      status.textContent = data?.mode === 'ai'
        ? 'Agent online · ' + (data.framework || 'LangChain') + ' · ' + (data.provider || '')
        : 'Agent · offline planner (no API key)';
    }
  } catch (e) {
    pending.textContent = demoReply(q);
    if (status) status.textContent = 'Assistant connection unavailable';
  } finally {
    busy = false;
    input.disabled = false;
    if (button) button.disabled = false;
    fit();
    scroll();
}
}

    form.addEventListener('submit',e=>{e.preventDefault();send(input.value)});
    input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();if(form.requestSubmit)form.requestSubmit();else send(input.value)}});input.addEventListener('input',fit);
    document.querySelectorAll('.suggestions [data-prompt]').forEach(b=>b.addEventListener('click',()=>send(b.dataset.prompt)));
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initNexoraChat);else initNexoraChat();
})();
