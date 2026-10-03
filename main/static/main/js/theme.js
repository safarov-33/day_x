const themeToggle = document.querySelector('.theme-toggle');

document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', event => {
        if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
});

themeToggle?.addEventListener('click', () => {
    const root = document.documentElement;
    const nextTheme = root.dataset.theme === 'dark' ? 'light' : 'dark';

    root.dataset.theme = nextTheme;
    try { localStorage.setItem('qarz-theme', nextTheme); } catch (error) {  }
});

const balancesElement = document.getElementById('debt-balances');
if (balancesElement) {
    const balances = JSON.parse(balancesElement.textContent);
    const debt = document.getElementById('id_debt');
    const amount = document.getElementById('id_amount');
    const panel = document.querySelector('.payment-balance');
    const updateBalance = () => {
        const balance = balances[debt.value];
        panel.hidden = !balance;
        if (balance) {
            document.getElementById('balance-value').textContent = balance;
            amount.max = balance;
        } else amount.removeAttribute('max');
    };
    debt.addEventListener('change', updateBalance);
    document.getElementById('pay-full').addEventListener('click', () => { amount.value = balances[debt.value]; });
    updateBalance();
}
document.querySelectorAll('nav a').forEach(link => {
    if (link.pathname === window.location.pathname) {
        link.classList.add('active');
        link.setAttribute('aria-current', 'page');
    }
});
