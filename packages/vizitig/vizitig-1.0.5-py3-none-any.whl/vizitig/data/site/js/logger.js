let log_holder = document.createElement("div");
document.body.prepend(log_holder);
log_holder.classList.add("w-100", "position-fixed", "top-0","z-3");

export class Logger {
    log(msg){
        console.log("log", msg);
    }

    error(msg){
        let error = document.createElement("div");
        error.classList.add("alert", "alert-danger","w-50", "alert-dismissible", "mx-auto", "z-3", "my-3");
        error.innerHTML = `${msg}
  <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`;
        log_holder.appendChild(error);
    }
    success(msg){
        let success = document.createElement("div");
        success.classList.add("alert", "alert-success","w-50", "alert-dismissible", "mx-auto", "z-3", "my-3");
        success.innerHTML = `${msg}  <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="close"></button>`;
        log_holder.appendChild(success);
        setTimeout(() => success.remove(), 1500);
    }

    warn(msg){
        let warn= document.createElement("div");
        warn.classList.add("alert", "alert-warning","w-50", "alert-dismissible", "mx-auto", "z-3", "my-3");
        warn.innerHTML = `${msg}  <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="close"></button>`;
        log_holder.appendChild(warn);
        setTimeout(() => warn.remove(), 1500);
        console.log("warn", msg)
    }
}
