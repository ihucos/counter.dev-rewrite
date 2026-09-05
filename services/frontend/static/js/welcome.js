let active = window.location.href.endsWith("?sign-up") ? 2 : 1;
initTabs(document.querySelector(".tabs"), { active: active });

simpleForm("#sign-in form[action='/login']", "/dashboard.html");
simpleForm("#modal-recover form[action='/recover']", () => {
    closeModal();
    notify("If the given mail and username matches, we will send you an mail with further instructions.");
});
simpleForm("#sign-up form", "/setup.html");

document.addEventListener("userloaded", () => {
    window.location.href = "dashboard.html";
});