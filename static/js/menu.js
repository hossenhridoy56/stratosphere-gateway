document.querySelectorAll('.dropdown').forEach(item => {
  item.addEventListener('click', () => {
    item.querySelector('.submenu').classList.toggle('active');
  });
});
function toggleMenu() {
  const menu = document.getElementById('mainMenu');
  menu.classList.toggle('active');
}