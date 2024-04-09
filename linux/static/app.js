

function type(filename){
    fetch(`/type/${filename}`, {
        method: 'GET',
    }).then(resp=>{
        window.resp = resp;
        return resp.text();
    }).then(t=>{
        console.log(t);
    });
}

function main(){
    let filter = modeljson.filter;
    let items = Array.from(document.querySelectorAll('button.item'));
    items.forEach((bt)=>{
        let filename = bt.textContent.trim();
        bt.addEventListener('click',(ev)=>{
            setTimeout(()=>{
                type(filename);
            },3000);
        })
        if (filter && filename.indexOf(filter)>=0){
            bt.classList.add('highlight');
        }
    });

    (()=>{
    //adjust flex/grid 
    //fill column first but height is dynamic while width is fixed
    let ul = document.querySelector('ul#list');
    let item_count = ul.querySelectorAll('li').length;
    let item_sample = ul.querySelector('li button');
    let item_w = item_sample.clientWidth;
    let item_h = item_sample.clientHeight;
    let vw = window.innerWidth;
    let columns = Math.floor(0.8*vw/item_w);
    let rows = Math.floor(item_count/columns);
    ul.style.height = `${rows*item_h+0.5*item_h}px`;
    })();
}

function on_ready(f) {
    document.addEventListener('DOMContentLoaded', f);
    if (document.readyState !== 'loading') {
        f();
    }
};
on_ready(main);