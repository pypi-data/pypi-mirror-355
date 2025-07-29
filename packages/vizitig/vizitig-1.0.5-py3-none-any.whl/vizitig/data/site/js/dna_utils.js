let DNA_Tr = new Map();
DNA_Tr.set("A", "T");
DNA_Tr.set("T", "A");
DNA_Tr.set("C", "G");
DNA_Tr.set("G", "C");

export function rc(sequence){
    return [...sequence].map((e)=> DNA_Tr.get(e)).reverse().join("")
}

export function canon(seq){
    let rev = rc(seq);
    if (rev < seq)
        return rev;
    else return seq;
}

export function extract_canonical_endpoint(sequence, k){
    let left  = canon(sequence.slice(0, k-1));
    let right = canon(sequence.slice(-k+1));
    if (left < right)
        return [left, right];
    return [right, left];
}
