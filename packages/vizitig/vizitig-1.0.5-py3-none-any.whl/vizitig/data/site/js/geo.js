function extract_pos(p){
    let np = {};
    np.x = p.px ? p.px:p.x;
    np.y = p.py ? p.py:p.y;
    return np;
}

export function barycenter(pos1, pos2, p){
    pos1 = extract_pos(pos1);
    pos2 = extract_pos(pos2);
    return {x:(p*pos1.x+(1-p)*pos2.x), y:(p*pos1.y+(1-p)*pos2.y)};
}

export function barycenter_many(positions){
    let bary = positions.map(extract_pos).reduce(function(bary, new_p){
            bary.x += new_p.x;
            bary.y += new_p.y;
            return bary;
        }, {x:0, y:0});
    bary.x = bary.x/positions.length;
    bary.y = bary.y/positions.length;
    return bary;
}

function norm(p){
    return Math.sqrt(Math.pow(p.x, 2) + Math.pow(p.y, 2))
}

function substr(p1, p2){
    return {x: p2.x - p1.x, y:p2.y-p1.y}
}

function vadd(p1, p2){
    return { x: p1.x + p2.x, y:p1.y+p2.y }
}

function vmul(shift, p){
    return { x: shift*p.x, y: shift*p.y };
}

function normalize(p){
    let n = norm(p)
    return {x: p.x/n, y:p.y/n};
}

const INF = {x: -1000, y:0};

export function shift_on_vector(p1, p2, shift){
    let v = normalize(substr(p1, p2));
    return vadd(p1, vmul(shift,v));
}

function perpendicular(p1, p2){
    p1 = extract_pos(p1);
    p2 = extract_pos(p2);
    if (norm(substr(p1, INF)) > norm(substr(p2, INF)))
        return perpendicular(p2, p1);
    let p = {x: p2.y - p1.y, y: p1.x - p2.x};
    let n = norm(p);
    return {x: p.x/n, y:p.y/n}
}

function barycenter_path(path){
    let npath = [];
    for (let i=1; i<path.length - 1; i++)
        npath.push(barycenter(path[i-1], path[i], 0));
    return npath;
}

function perpendical_vect(path){
    let npath = [];
    for (let i=1; i<path.length; i++)
        npath.push(perpendicular(path[i-1], path[i]));
    return npath;
}


export function parallel_path(path, amplitude){
    let vpath = perpendical_vect(path);
    let ppath = [];
    for (let i=0; i<path.length-1; i++){
        let p1 = {x: path[i  ].x +amplitude*vpath[i].x, y: path[i  ].y   + amplitude*vpath[i].y};
        let p2 = {x: path[i+1].x +amplitude*vpath[i].x, y: path[i+1].y   + amplitude*vpath[i].y};
        ppath.push([p1, p2]);
    }
    return ppath;
}

