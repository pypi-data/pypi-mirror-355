import { i as zt, a as Te, r as Bt, w as Q, g as Dt, c as J } from "./Index-Bsbz4ASv.js";
const _ = window.ms_globals.React, jt = window.ms_globals.React.version, kt = window.ms_globals.React.forwardRef, Rt = window.ms_globals.React.useRef, Lt = window.ms_globals.React.useState, At = window.ms_globals.React.useEffect, Ht = window.ms_globals.React.useMemo, we = window.ms_globals.ReactDOM.createPortal, Xt = window.ms_globals.internalContext.useContextPropsContext, De = window.ms_globals.internalContext.ContextPropsProvider, $t = window.ms_globals.createItemsContext.createItemsContext, Ft = window.ms_globals.antd.ConfigProvider, Vt = window.ms_globals.antd.Dropdown, Oe = window.ms_globals.antd.theme, Nt = window.ms_globals.antd.Tooltip, Gt = window.ms_globals.antdIcons.EllipsisOutlined, Xe = window.ms_globals.antdCssinjs.unit, ye = window.ms_globals.antdCssinjs.token2CSSVar, $e = window.ms_globals.antdCssinjs.useStyleRegister, Ut = window.ms_globals.antdCssinjs.useCSSVarRegister, Wt = window.ms_globals.antdCssinjs.createTheme, qt = window.ms_globals.antdCssinjs.useCacheToken;
var Kt = /\s/;
function Qt(t) {
  for (var e = t.length; e-- && Kt.test(t.charAt(e)); )
    ;
  return e;
}
var Jt = /^\s+/;
function Zt(t) {
  return t && t.slice(0, Qt(t) + 1).replace(Jt, "");
}
var Fe = NaN, Yt = /^[-+]0x[0-9a-f]+$/i, er = /^0b[01]+$/i, tr = /^0o[0-7]+$/i, rr = parseInt;
function Ve(t) {
  if (typeof t == "number")
    return t;
  if (zt(t))
    return Fe;
  if (Te(t)) {
    var e = typeof t.valueOf == "function" ? t.valueOf() : t;
    t = Te(e) ? e + "" : e;
  }
  if (typeof t != "string")
    return t === 0 ? t : +t;
  t = Zt(t);
  var n = er.test(t);
  return n || tr.test(t) ? rr(t.slice(2), n ? 2 : 8) : Yt.test(t) ? Fe : +t;
}
var ve = function() {
  return Bt.Date.now();
}, nr = "Expected a function", or = Math.max, ir = Math.min;
function sr(t, e, n) {
  var o, r, i, s, a, l, c = 0, u = !1, f = !1, d = !0;
  if (typeof t != "function")
    throw new TypeError(nr);
  e = Ve(e) || 0, Te(n) && (u = !!n.leading, f = "maxWait" in n, i = f ? or(Ve(n.maxWait) || 0, e) : i, d = "trailing" in n ? !!n.trailing : d);
  function p(m) {
    var w = o, O = r;
    return o = r = void 0, c = m, s = t.apply(O, w), s;
  }
  function y(m) {
    return c = m, a = setTimeout(b, e), u ? p(m) : s;
  }
  function x(m) {
    var w = m - l, O = m - c, P = e - w;
    return f ? ir(P, i - O) : P;
  }
  function g(m) {
    var w = m - l, O = m - c;
    return l === void 0 || w >= e || w < 0 || f && O >= i;
  }
  function b() {
    var m = ve();
    if (g(m))
      return C(m);
    a = setTimeout(b, x(m));
  }
  function C(m) {
    return a = void 0, d && o ? p(m) : (o = r = void 0, s);
  }
  function E() {
    a !== void 0 && clearTimeout(a), c = 0, o = l = r = a = void 0;
  }
  function h() {
    return a === void 0 ? s : C(ve());
  }
  function v() {
    var m = ve(), w = g(m);
    if (o = arguments, r = this, l = m, w) {
      if (a === void 0)
        return y(l);
      if (f)
        return clearTimeout(a), a = setTimeout(b, e), p(l);
    }
    return a === void 0 && (a = setTimeout(b, e)), s;
  }
  return v.cancel = E, v.flush = h, v;
}
var at = {
  exports: {}
}, oe = {};
/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var ar = _, lr = Symbol.for("react.element"), cr = Symbol.for("react.fragment"), ur = Object.prototype.hasOwnProperty, fr = ar.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner, dr = {
  key: !0,
  ref: !0,
  __self: !0,
  __source: !0
};
function lt(t, e, n) {
  var o, r = {}, i = null, s = null;
  n !== void 0 && (i = "" + n), e.key !== void 0 && (i = "" + e.key), e.ref !== void 0 && (s = e.ref);
  for (o in e) ur.call(e, o) && !dr.hasOwnProperty(o) && (r[o] = e[o]);
  if (t && t.defaultProps) for (o in e = t.defaultProps, e) r[o] === void 0 && (r[o] = e[o]);
  return {
    $$typeof: lr,
    type: t,
    key: i,
    ref: s,
    props: r,
    _owner: fr.current
  };
}
oe.Fragment = cr;
oe.jsx = lt;
oe.jsxs = lt;
at.exports = oe;
var z = at.exports;
const {
  SvelteComponent: hr,
  assign: Ne,
  binding_callbacks: Ge,
  check_outros: gr,
  children: ct,
  claim_element: ut,
  claim_space: pr,
  component_subscribe: Ue,
  compute_slots: mr,
  create_slot: br,
  detach: V,
  element: ft,
  empty: We,
  exclude_internal_props: qe,
  get_all_dirty_from_scope: yr,
  get_slot_changes: vr,
  group_outros: xr,
  init: Sr,
  insert_hydration: Z,
  safe_not_equal: _r,
  set_custom_element_data: dt,
  space: Cr,
  transition_in: Y,
  transition_out: Me,
  update_slot_base: wr
} = window.__gradio__svelte__internal, {
  beforeUpdate: Tr,
  getContext: Or,
  onDestroy: Mr,
  setContext: Pr
} = window.__gradio__svelte__internal;
function Ke(t) {
  let e, n;
  const o = (
    /*#slots*/
    t[7].default
  ), r = br(
    o,
    t,
    /*$$scope*/
    t[6],
    null
  );
  return {
    c() {
      e = ft("svelte-slot"), r && r.c(), this.h();
    },
    l(i) {
      e = ut(i, "SVELTE-SLOT", {
        class: !0
      });
      var s = ct(e);
      r && r.l(s), s.forEach(V), this.h();
    },
    h() {
      dt(e, "class", "svelte-1rt0kpf");
    },
    m(i, s) {
      Z(i, e, s), r && r.m(e, null), t[9](e), n = !0;
    },
    p(i, s) {
      r && r.p && (!n || s & /*$$scope*/
      64) && wr(
        r,
        o,
        i,
        /*$$scope*/
        i[6],
        n ? vr(
          o,
          /*$$scope*/
          i[6],
          s,
          null
        ) : yr(
          /*$$scope*/
          i[6]
        ),
        null
      );
    },
    i(i) {
      n || (Y(r, i), n = !0);
    },
    o(i) {
      Me(r, i), n = !1;
    },
    d(i) {
      i && V(e), r && r.d(i), t[9](null);
    }
  };
}
function Er(t) {
  let e, n, o, r, i = (
    /*$$slots*/
    t[4].default && Ke(t)
  );
  return {
    c() {
      e = ft("react-portal-target"), n = Cr(), i && i.c(), o = We(), this.h();
    },
    l(s) {
      e = ut(s, "REACT-PORTAL-TARGET", {
        class: !0
      }), ct(e).forEach(V), n = pr(s), i && i.l(s), o = We(), this.h();
    },
    h() {
      dt(e, "class", "svelte-1rt0kpf");
    },
    m(s, a) {
      Z(s, e, a), t[8](e), Z(s, n, a), i && i.m(s, a), Z(s, o, a), r = !0;
    },
    p(s, [a]) {
      /*$$slots*/
      s[4].default ? i ? (i.p(s, a), a & /*$$slots*/
      16 && Y(i, 1)) : (i = Ke(s), i.c(), Y(i, 1), i.m(o.parentNode, o)) : i && (xr(), Me(i, 1, 1, () => {
        i = null;
      }), gr());
    },
    i(s) {
      r || (Y(i), r = !0);
    },
    o(s) {
      Me(i), r = !1;
    },
    d(s) {
      s && (V(e), V(n), V(o)), t[8](null), i && i.d(s);
    }
  };
}
function Qe(t) {
  const {
    svelteInit: e,
    ...n
  } = t;
  return n;
}
function Ir(t, e, n) {
  let o, r, {
    $$slots: i = {},
    $$scope: s
  } = e;
  const a = mr(i);
  let {
    svelteInit: l
  } = e;
  const c = Q(Qe(e)), u = Q();
  Ue(t, u, (h) => n(0, o = h));
  const f = Q();
  Ue(t, f, (h) => n(1, r = h));
  const d = [], p = Or("$$ms-gr-react-wrapper"), {
    slotKey: y,
    slotIndex: x,
    subSlotIndex: g
  } = Dt() || {}, b = l({
    parent: p,
    props: c,
    target: u,
    slot: f,
    slotKey: y,
    slotIndex: x,
    subSlotIndex: g,
    onDestroy(h) {
      d.push(h);
    }
  });
  Pr("$$ms-gr-react-wrapper", b), Tr(() => {
    c.set(Qe(e));
  }), Mr(() => {
    d.forEach((h) => h());
  });
  function C(h) {
    Ge[h ? "unshift" : "push"](() => {
      o = h, u.set(o);
    });
  }
  function E(h) {
    Ge[h ? "unshift" : "push"](() => {
      r = h, f.set(r);
    });
  }
  return t.$$set = (h) => {
    n(17, e = Ne(Ne({}, e), qe(h))), "svelteInit" in h && n(5, l = h.svelteInit), "$$scope" in h && n(6, s = h.$$scope);
  }, e = qe(e), [o, r, u, f, a, l, s, i, C, E];
}
class jr extends hr {
  constructor(e) {
    super(), Sr(this, e, Ir, Er, _r, {
      svelteInit: 5
    });
  }
}
const {
  SvelteComponent: En
} = window.__gradio__svelte__internal, Je = window.ms_globals.rerender, xe = window.ms_globals.tree;
function kr(t, e = {}) {
  function n(o) {
    const r = Q(), i = new jr({
      ...o,
      props: {
        svelteInit(s) {
          window.ms_globals.autokey += 1;
          const a = {
            key: window.ms_globals.autokey,
            svelteInstance: r,
            reactComponent: t,
            props: s.props,
            slot: s.slot,
            target: s.target,
            slotIndex: s.slotIndex,
            subSlotIndex: s.subSlotIndex,
            ignore: e.ignore,
            slotKey: s.slotKey,
            nodes: []
          }, l = s.parent ?? xe;
          return l.nodes = [...l.nodes, a], Je({
            createPortal: we,
            node: xe
          }), s.onDestroy(() => {
            l.nodes = l.nodes.filter((c) => c.svelteInstance !== r), Je({
              createPortal: we,
              node: xe
            });
          }), a;
        },
        ...o.props
      }
    });
    return r.set(i), i;
  }
  return new Promise((o) => {
    window.ms_globals.initializePromise.then(() => {
      o(n);
    });
  });
}
const Rr = "1.4.0";
function te() {
  return te = Object.assign ? Object.assign.bind() : function(t) {
    for (var e = 1; e < arguments.length; e++) {
      var n = arguments[e];
      for (var o in n) ({}).hasOwnProperty.call(n, o) && (t[o] = n[o]);
    }
    return t;
  }, te.apply(null, arguments);
}
const Lr = /* @__PURE__ */ _.createContext({}), Ar = {
  classNames: {},
  styles: {},
  className: "",
  style: {}
}, Hr = (t) => {
  const e = _.useContext(Lr);
  return _.useMemo(() => ({
    ...Ar,
    ...e[t]
  }), [e[t]]);
};
function re() {
  const {
    getPrefixCls: t,
    direction: e,
    csp: n,
    iconPrefixCls: o,
    theme: r
  } = _.useContext(Ft.ConfigContext);
  return {
    theme: r,
    getPrefixCls: t,
    direction: e,
    csp: n,
    iconPrefixCls: o
  };
}
const G = (t, e) => {
  const n = t[0];
  for (const o of e)
    if (o.key === n) {
      if (t.length === 1) return o;
      if ("children" in o)
        return G(t.slice(1), o.children);
    }
  return null;
}, zr = (t) => {
  const {
    onClick: e,
    item: n
  } = t, {
    children: o = [],
    triggerSubMenuAction: r = "hover"
  } = n, {
    getPrefixCls: i
  } = re(), s = i("actions", t.prefixCls), a = (n == null ? void 0 : n.icon) ?? /* @__PURE__ */ _.createElement(Gt, null), l = {
    items: o,
    onClick: ({
      key: c,
      keyPath: u,
      domEvent: f
    }) => {
      var d, p, y;
      if ((d = G(u, o)) != null && d.onItemClick) {
        (y = (p = G(u, o)) == null ? void 0 : p.onItemClick) == null || y.call(p, G(u, o));
        return;
      }
      e == null || e({
        key: c,
        keyPath: [...u, n.key],
        domEvent: f,
        item: G(u, o)
      });
    }
  };
  return /* @__PURE__ */ _.createElement(Vt, {
    menu: l,
    overlayClassName: `${s}-sub-item`,
    arrow: !0,
    trigger: [r]
  }, /* @__PURE__ */ _.createElement("div", {
    className: `${s}-list-item`
  }, /* @__PURE__ */ _.createElement("div", {
    className: `${s}-list-item-icon`
  }, a)));
};
function A(t) {
  "@babel/helpers - typeof";
  return A = typeof Symbol == "function" && typeof Symbol.iterator == "symbol" ? function(e) {
    return typeof e;
  } : function(e) {
    return e && typeof Symbol == "function" && e.constructor === Symbol && e !== Symbol.prototype ? "symbol" : typeof e;
  }, A(t);
}
function Br(t) {
  if (Array.isArray(t)) return t;
}
function Dr(t, e) {
  var n = t == null ? null : typeof Symbol < "u" && t[Symbol.iterator] || t["@@iterator"];
  if (n != null) {
    var o, r, i, s, a = [], l = !0, c = !1;
    try {
      if (i = (n = n.call(t)).next, e === 0) {
        if (Object(n) !== n) return;
        l = !1;
      } else for (; !(l = (o = i.call(n)).done) && (a.push(o.value), a.length !== e); l = !0) ;
    } catch (u) {
      c = !0, r = u;
    } finally {
      try {
        if (!l && n.return != null && (s = n.return(), Object(s) !== s)) return;
      } finally {
        if (c) throw r;
      }
    }
    return a;
  }
}
function Ze(t, e) {
  (e == null || e > t.length) && (e = t.length);
  for (var n = 0, o = Array(e); n < e; n++) o[n] = t[n];
  return o;
}
function Xr(t, e) {
  if (t) {
    if (typeof t == "string") return Ze(t, e);
    var n = {}.toString.call(t).slice(8, -1);
    return n === "Object" && t.constructor && (n = t.constructor.name), n === "Map" || n === "Set" ? Array.from(t) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Ze(t, e) : void 0;
  }
}
function $r() {
  throw new TypeError(`Invalid attempt to destructure non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`);
}
function ee(t, e) {
  return Br(t) || Dr(t, e) || Xr(t, e) || $r();
}
function Fr(t, e) {
  if (A(t) != "object" || !t) return t;
  var n = t[Symbol.toPrimitive];
  if (n !== void 0) {
    var o = n.call(t, e);
    if (A(o) != "object") return o;
    throw new TypeError("@@toPrimitive must return a primitive value.");
  }
  return (e === "string" ? String : Number)(t);
}
function ht(t) {
  var e = Fr(t, "string");
  return A(e) == "symbol" ? e : e + "";
}
function T(t, e, n) {
  return (e = ht(e)) in t ? Object.defineProperty(t, e, {
    value: n,
    enumerable: !0,
    configurable: !0,
    writable: !0
  }) : t[e] = n, t;
}
function Ye(t, e) {
  var n = Object.keys(t);
  if (Object.getOwnPropertySymbols) {
    var o = Object.getOwnPropertySymbols(t);
    e && (o = o.filter(function(r) {
      return Object.getOwnPropertyDescriptor(t, r).enumerable;
    })), n.push.apply(n, o);
  }
  return n;
}
function j(t) {
  for (var e = 1; e < arguments.length; e++) {
    var n = arguments[e] != null ? arguments[e] : {};
    e % 2 ? Ye(Object(n), !0).forEach(function(o) {
      T(t, o, n[o]);
    }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(t, Object.getOwnPropertyDescriptors(n)) : Ye(Object(n)).forEach(function(o) {
      Object.defineProperty(t, o, Object.getOwnPropertyDescriptor(n, o));
    });
  }
  return t;
}
function ie(t, e) {
  if (!(t instanceof e)) throw new TypeError("Cannot call a class as a function");
}
function Vr(t, e) {
  for (var n = 0; n < e.length; n++) {
    var o = e[n];
    o.enumerable = o.enumerable || !1, o.configurable = !0, "value" in o && (o.writable = !0), Object.defineProperty(t, ht(o.key), o);
  }
}
function se(t, e, n) {
  return e && Vr(t.prototype, e), Object.defineProperty(t, "prototype", {
    writable: !1
  }), t;
}
function U(t) {
  if (t === void 0) throw new ReferenceError("this hasn't been initialised - super() hasn't been called");
  return t;
}
function Pe(t, e) {
  return Pe = Object.setPrototypeOf ? Object.setPrototypeOf.bind() : function(n, o) {
    return n.__proto__ = o, n;
  }, Pe(t, e);
}
function gt(t, e) {
  if (typeof e != "function" && e !== null) throw new TypeError("Super expression must either be null or a function");
  t.prototype = Object.create(e && e.prototype, {
    constructor: {
      value: t,
      writable: !0,
      configurable: !0
    }
  }), Object.defineProperty(t, "prototype", {
    writable: !1
  }), e && Pe(t, e);
}
function ne(t) {
  return ne = Object.setPrototypeOf ? Object.getPrototypeOf.bind() : function(e) {
    return e.__proto__ || Object.getPrototypeOf(e);
  }, ne(t);
}
function pt() {
  try {
    var t = !Boolean.prototype.valueOf.call(Reflect.construct(Boolean, [], function() {
    }));
  } catch {
  }
  return (pt = function() {
    return !!t;
  })();
}
function Nr(t, e) {
  if (e && (A(e) == "object" || typeof e == "function")) return e;
  if (e !== void 0) throw new TypeError("Derived constructors may only return object or undefined");
  return U(t);
}
function mt(t) {
  var e = pt();
  return function() {
    var n, o = ne(t);
    if (e) {
      var r = ne(this).constructor;
      n = Reflect.construct(o, arguments, r);
    } else n = o.apply(this, arguments);
    return Nr(this, n);
  };
}
var bt = /* @__PURE__ */ se(function t() {
  ie(this, t);
}), yt = "CALC_UNIT", Gr = new RegExp(yt, "g");
function Se(t) {
  return typeof t == "number" ? "".concat(t).concat(yt) : t;
}
var Ur = /* @__PURE__ */ function(t) {
  gt(n, t);
  var e = mt(n);
  function n(o, r) {
    var i;
    ie(this, n), i = e.call(this), T(U(i), "result", ""), T(U(i), "unitlessCssVar", void 0), T(U(i), "lowPriority", void 0);
    var s = A(o);
    return i.unitlessCssVar = r, o instanceof n ? i.result = "(".concat(o.result, ")") : s === "number" ? i.result = Se(o) : s === "string" && (i.result = o), i;
  }
  return se(n, [{
    key: "add",
    value: function(r) {
      return r instanceof n ? this.result = "".concat(this.result, " + ").concat(r.getResult()) : (typeof r == "number" || typeof r == "string") && (this.result = "".concat(this.result, " + ").concat(Se(r))), this.lowPriority = !0, this;
    }
  }, {
    key: "sub",
    value: function(r) {
      return r instanceof n ? this.result = "".concat(this.result, " - ").concat(r.getResult()) : (typeof r == "number" || typeof r == "string") && (this.result = "".concat(this.result, " - ").concat(Se(r))), this.lowPriority = !0, this;
    }
  }, {
    key: "mul",
    value: function(r) {
      return this.lowPriority && (this.result = "(".concat(this.result, ")")), r instanceof n ? this.result = "".concat(this.result, " * ").concat(r.getResult(!0)) : (typeof r == "number" || typeof r == "string") && (this.result = "".concat(this.result, " * ").concat(r)), this.lowPriority = !1, this;
    }
  }, {
    key: "div",
    value: function(r) {
      return this.lowPriority && (this.result = "(".concat(this.result, ")")), r instanceof n ? this.result = "".concat(this.result, " / ").concat(r.getResult(!0)) : (typeof r == "number" || typeof r == "string") && (this.result = "".concat(this.result, " / ").concat(r)), this.lowPriority = !1, this;
    }
  }, {
    key: "getResult",
    value: function(r) {
      return this.lowPriority || r ? "(".concat(this.result, ")") : this.result;
    }
  }, {
    key: "equal",
    value: function(r) {
      var i = this, s = r || {}, a = s.unit, l = !0;
      return typeof a == "boolean" ? l = a : Array.from(this.unitlessCssVar).some(function(c) {
        return i.result.includes(c);
      }) && (l = !1), this.result = this.result.replace(Gr, l ? "px" : ""), typeof this.lowPriority < "u" ? "calc(".concat(this.result, ")") : this.result;
    }
  }]), n;
}(bt), Wr = /* @__PURE__ */ function(t) {
  gt(n, t);
  var e = mt(n);
  function n(o) {
    var r;
    return ie(this, n), r = e.call(this), T(U(r), "result", 0), o instanceof n ? r.result = o.result : typeof o == "number" && (r.result = o), r;
  }
  return se(n, [{
    key: "add",
    value: function(r) {
      return r instanceof n ? this.result += r.result : typeof r == "number" && (this.result += r), this;
    }
  }, {
    key: "sub",
    value: function(r) {
      return r instanceof n ? this.result -= r.result : typeof r == "number" && (this.result -= r), this;
    }
  }, {
    key: "mul",
    value: function(r) {
      return r instanceof n ? this.result *= r.result : typeof r == "number" && (this.result *= r), this;
    }
  }, {
    key: "div",
    value: function(r) {
      return r instanceof n ? this.result /= r.result : typeof r == "number" && (this.result /= r), this;
    }
  }, {
    key: "equal",
    value: function() {
      return this.result;
    }
  }]), n;
}(bt), qr = function(e, n) {
  var o = e === "css" ? Ur : Wr;
  return function(r) {
    return new o(r, n);
  };
}, et = function(e, n) {
  return "".concat([n, e.replace(/([A-Z]+)([A-Z][a-z]+)/g, "$1-$2").replace(/([a-z])([A-Z])/g, "$1-$2")].filter(Boolean).join("-"));
}, S = {};
/**
 * @license React
 * react-is.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var je = Symbol.for("react.element"), ke = Symbol.for("react.portal"), ae = Symbol.for("react.fragment"), le = Symbol.for("react.strict_mode"), ce = Symbol.for("react.profiler"), ue = Symbol.for("react.provider"), fe = Symbol.for("react.context"), Kr = Symbol.for("react.server_context"), de = Symbol.for("react.forward_ref"), he = Symbol.for("react.suspense"), ge = Symbol.for("react.suspense_list"), pe = Symbol.for("react.memo"), me = Symbol.for("react.lazy"), Qr = Symbol.for("react.offscreen"), vt;
vt = Symbol.for("react.module.reference");
function R(t) {
  if (typeof t == "object" && t !== null) {
    var e = t.$$typeof;
    switch (e) {
      case je:
        switch (t = t.type, t) {
          case ae:
          case ce:
          case le:
          case he:
          case ge:
            return t;
          default:
            switch (t = t && t.$$typeof, t) {
              case Kr:
              case fe:
              case de:
              case me:
              case pe:
              case ue:
                return t;
              default:
                return e;
            }
        }
      case ke:
        return e;
    }
  }
}
S.ContextConsumer = fe;
S.ContextProvider = ue;
S.Element = je;
S.ForwardRef = de;
S.Fragment = ae;
S.Lazy = me;
S.Memo = pe;
S.Portal = ke;
S.Profiler = ce;
S.StrictMode = le;
S.Suspense = he;
S.SuspenseList = ge;
S.isAsyncMode = function() {
  return !1;
};
S.isConcurrentMode = function() {
  return !1;
};
S.isContextConsumer = function(t) {
  return R(t) === fe;
};
S.isContextProvider = function(t) {
  return R(t) === ue;
};
S.isElement = function(t) {
  return typeof t == "object" && t !== null && t.$$typeof === je;
};
S.isForwardRef = function(t) {
  return R(t) === de;
};
S.isFragment = function(t) {
  return R(t) === ae;
};
S.isLazy = function(t) {
  return R(t) === me;
};
S.isMemo = function(t) {
  return R(t) === pe;
};
S.isPortal = function(t) {
  return R(t) === ke;
};
S.isProfiler = function(t) {
  return R(t) === ce;
};
S.isStrictMode = function(t) {
  return R(t) === le;
};
S.isSuspense = function(t) {
  return R(t) === he;
};
S.isSuspenseList = function(t) {
  return R(t) === ge;
};
S.isValidElementType = function(t) {
  return typeof t == "string" || typeof t == "function" || t === ae || t === ce || t === le || t === he || t === ge || t === Qr || typeof t == "object" && t !== null && (t.$$typeof === me || t.$$typeof === pe || t.$$typeof === ue || t.$$typeof === fe || t.$$typeof === de || t.$$typeof === vt || t.getModuleId !== void 0);
};
S.typeOf = R;
Number(jt.split(".")[0]);
function tt(t, e, n, o) {
  var r = j({}, e[t]);
  if (o != null && o.deprecatedTokens) {
    var i = o.deprecatedTokens;
    i.forEach(function(a) {
      var l = ee(a, 2), c = l[0], u = l[1];
      if (r != null && r[c] || r != null && r[u]) {
        var f;
        (f = r[u]) !== null && f !== void 0 || (r[u] = r == null ? void 0 : r[c]);
      }
    });
  }
  var s = j(j({}, n), r);
  return Object.keys(s).forEach(function(a) {
    s[a] === e[a] && delete s[a];
  }), s;
}
var xt = typeof CSSINJS_STATISTIC < "u", Ee = !0;
function Re() {
  for (var t = arguments.length, e = new Array(t), n = 0; n < t; n++)
    e[n] = arguments[n];
  if (!xt)
    return Object.assign.apply(Object, [{}].concat(e));
  Ee = !1;
  var o = {};
  return e.forEach(function(r) {
    if (A(r) === "object") {
      var i = Object.keys(r);
      i.forEach(function(s) {
        Object.defineProperty(o, s, {
          configurable: !0,
          enumerable: !0,
          get: function() {
            return r[s];
          }
        });
      });
    }
  }), Ee = !0, o;
}
var rt = {};
function Jr() {
}
var Zr = function(e) {
  var n, o = e, r = Jr;
  return xt && typeof Proxy < "u" && (n = /* @__PURE__ */ new Set(), o = new Proxy(e, {
    get: function(s, a) {
      if (Ee) {
        var l;
        (l = n) === null || l === void 0 || l.add(a);
      }
      return s[a];
    }
  }), r = function(s, a) {
    var l;
    rt[s] = {
      global: Array.from(n),
      component: j(j({}, (l = rt[s]) === null || l === void 0 ? void 0 : l.component), a)
    };
  }), {
    token: o,
    keys: n,
    flush: r
  };
};
function nt(t, e, n) {
  if (typeof n == "function") {
    var o;
    return n(Re(e, (o = e[t]) !== null && o !== void 0 ? o : {}));
  }
  return n ?? {};
}
function Yr(t) {
  return t === "js" ? {
    max: Math.max,
    min: Math.min
  } : {
    max: function() {
      for (var n = arguments.length, o = new Array(n), r = 0; r < n; r++)
        o[r] = arguments[r];
      return "max(".concat(o.map(function(i) {
        return Xe(i);
      }).join(","), ")");
    },
    min: function() {
      for (var n = arguments.length, o = new Array(n), r = 0; r < n; r++)
        o[r] = arguments[r];
      return "min(".concat(o.map(function(i) {
        return Xe(i);
      }).join(","), ")");
    }
  };
}
var en = 1e3 * 60 * 10, tn = /* @__PURE__ */ function() {
  function t() {
    ie(this, t), T(this, "map", /* @__PURE__ */ new Map()), T(this, "objectIDMap", /* @__PURE__ */ new WeakMap()), T(this, "nextID", 0), T(this, "lastAccessBeat", /* @__PURE__ */ new Map()), T(this, "accessBeat", 0);
  }
  return se(t, [{
    key: "set",
    value: function(n, o) {
      this.clear();
      var r = this.getCompositeKey(n);
      this.map.set(r, o), this.lastAccessBeat.set(r, Date.now());
    }
  }, {
    key: "get",
    value: function(n) {
      var o = this.getCompositeKey(n), r = this.map.get(o);
      return this.lastAccessBeat.set(o, Date.now()), this.accessBeat += 1, r;
    }
  }, {
    key: "getCompositeKey",
    value: function(n) {
      var o = this, r = n.map(function(i) {
        return i && A(i) === "object" ? "obj_".concat(o.getObjectID(i)) : "".concat(A(i), "_").concat(i);
      });
      return r.join("|");
    }
  }, {
    key: "getObjectID",
    value: function(n) {
      if (this.objectIDMap.has(n))
        return this.objectIDMap.get(n);
      var o = this.nextID;
      return this.objectIDMap.set(n, o), this.nextID += 1, o;
    }
  }, {
    key: "clear",
    value: function() {
      var n = this;
      if (this.accessBeat > 1e4) {
        var o = Date.now();
        this.lastAccessBeat.forEach(function(r, i) {
          o - r > en && (n.map.delete(i), n.lastAccessBeat.delete(i));
        }), this.accessBeat = 0;
      }
    }
  }]), t;
}(), ot = new tn();
function rn(t, e) {
  return _.useMemo(function() {
    var n = ot.get(e);
    if (n)
      return n;
    var o = t();
    return ot.set(e, o), o;
  }, e);
}
var nn = function() {
  return {};
};
function on(t) {
  var e = t.useCSP, n = e === void 0 ? nn : e, o = t.useToken, r = t.usePrefix, i = t.getResetStyles, s = t.getCommonStyle, a = t.getCompUnitless;
  function l(d, p, y, x) {
    var g = Array.isArray(d) ? d[0] : d;
    function b(O) {
      return "".concat(String(g)).concat(O.slice(0, 1).toUpperCase()).concat(O.slice(1));
    }
    var C = (x == null ? void 0 : x.unitless) || {}, E = typeof a == "function" ? a(d) : {}, h = j(j({}, E), {}, T({}, b("zIndexPopup"), !0));
    Object.keys(C).forEach(function(O) {
      h[b(O)] = C[O];
    });
    var v = j(j({}, x), {}, {
      unitless: h,
      prefixToken: b
    }), m = u(d, p, y, v), w = c(g, y, v);
    return function(O) {
      var P = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : O, L = m(O, P), D = ee(L, 2), I = D[1], X = w(P), k = ee(X, 2), H = k[0], W = k[1];
      return [H, I, W];
    };
  }
  function c(d, p, y) {
    var x = y.unitless, g = y.injectStyle, b = g === void 0 ? !0 : g, C = y.prefixToken, E = y.ignore, h = function(w) {
      var O = w.rootCls, P = w.cssVar, L = P === void 0 ? {} : P, D = o(), I = D.realToken;
      return Ut({
        path: [d],
        prefix: L.prefix,
        key: L.key,
        unitless: x,
        ignore: E,
        token: I,
        scope: O
      }, function() {
        var X = nt(d, I, p), k = tt(d, I, X, {
          deprecatedTokens: y == null ? void 0 : y.deprecatedTokens
        });
        return Object.keys(X).forEach(function(H) {
          k[C(H)] = k[H], delete k[H];
        }), k;
      }), null;
    }, v = function(w) {
      var O = o(), P = O.cssVar;
      return [function(L) {
        return b && P ? /* @__PURE__ */ _.createElement(_.Fragment, null, /* @__PURE__ */ _.createElement(h, {
          rootCls: w,
          cssVar: P,
          component: d
        }), L) : L;
      }, P == null ? void 0 : P.key];
    };
    return v;
  }
  function u(d, p, y) {
    var x = arguments.length > 3 && arguments[3] !== void 0 ? arguments[3] : {}, g = Array.isArray(d) ? d : [d, d], b = ee(g, 1), C = b[0], E = g.join("-"), h = t.layer || {
      name: "antd"
    };
    return function(v) {
      var m = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : v, w = o(), O = w.theme, P = w.realToken, L = w.hashId, D = w.token, I = w.cssVar, X = r(), k = X.rootPrefixCls, H = X.iconPrefixCls, W = n(), be = I ? "css" : "js", Ct = rn(function() {
        var $ = /* @__PURE__ */ new Set();
        return I && Object.keys(x.unitless || {}).forEach(function(q) {
          $.add(ye(q, I.prefix)), $.add(ye(q, et(C, I.prefix)));
        }), qr(be, $);
      }, [be, C, I == null ? void 0 : I.prefix]), Le = Yr(be), wt = Le.max, Tt = Le.min, Ae = {
        theme: O,
        token: D,
        hashId: L,
        nonce: function() {
          return W.nonce;
        },
        clientOnly: x.clientOnly,
        layer: h,
        // antd is always at top of styles
        order: x.order || -999
      };
      typeof i == "function" && $e(j(j({}, Ae), {}, {
        clientOnly: !1,
        path: ["Shared", k]
      }), function() {
        return i(D, {
          prefix: {
            rootPrefixCls: k,
            iconPrefixCls: H
          },
          csp: W
        });
      });
      var Ot = $e(j(j({}, Ae), {}, {
        path: [E, v, H]
      }), function() {
        if (x.injectStyle === !1)
          return [];
        var $ = Zr(D), q = $.token, Mt = $.flush, F = nt(C, P, y), Pt = ".".concat(v), He = tt(C, P, F, {
          deprecatedTokens: x.deprecatedTokens
        });
        I && F && A(F) === "object" && Object.keys(F).forEach(function(Be) {
          F[Be] = "var(".concat(ye(Be, et(C, I.prefix)), ")");
        });
        var ze = Re(q, {
          componentCls: Pt,
          prefixCls: v,
          iconCls: ".".concat(H),
          antCls: ".".concat(k),
          calc: Ct,
          // @ts-ignore
          max: wt,
          // @ts-ignore
          min: Tt
        }, I ? F : He), Et = p(ze, {
          hashId: L,
          prefixCls: v,
          rootPrefixCls: k,
          iconPrefixCls: H
        });
        Mt(C, He);
        var It = typeof s == "function" ? s(ze, v, m, x.resetFont) : null;
        return [x.resetStyle === !1 ? null : It, Et];
      });
      return [Ot, L];
    };
  }
  function f(d, p, y) {
    var x = arguments.length > 3 && arguments[3] !== void 0 ? arguments[3] : {}, g = u(d, p, y, j({
      resetStyle: !1,
      // Sub Style should default after root one
      order: -998
    }, x)), b = function(E) {
      var h = E.prefixCls, v = E.rootCls, m = v === void 0 ? h : v;
      return g(h, m), null;
    };
    return b;
  }
  return {
    genStyleHooks: l,
    genSubStyleComponent: f,
    genComponentStyleHook: u
  };
}
const sn = {
  blue: "#1677FF",
  purple: "#722ED1",
  cyan: "#13C2C2",
  green: "#52C41A",
  magenta: "#EB2F96",
  /**
   * @deprecated Use magenta instead
   */
  pink: "#EB2F96",
  red: "#F5222D",
  orange: "#FA8C16",
  yellow: "#FADB14",
  volcano: "#FA541C",
  geekblue: "#2F54EB",
  gold: "#FAAD14",
  lime: "#A0D911"
}, an = Object.assign(Object.assign({}, sn), {
  // Color
  colorPrimary: "#1677ff",
  colorSuccess: "#52c41a",
  colorWarning: "#faad14",
  colorError: "#ff4d4f",
  colorInfo: "#1677ff",
  colorLink: "",
  colorTextBase: "",
  colorBgBase: "",
  // Font
  fontFamily: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
'Noto Color Emoji'`,
  fontFamilyCode: "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace",
  fontSize: 14,
  // Line
  lineWidth: 1,
  lineType: "solid",
  // Motion
  motionUnit: 0.1,
  motionBase: 0,
  motionEaseOutCirc: "cubic-bezier(0.08, 0.82, 0.17, 1)",
  motionEaseInOutCirc: "cubic-bezier(0.78, 0.14, 0.15, 0.86)",
  motionEaseOut: "cubic-bezier(0.215, 0.61, 0.355, 1)",
  motionEaseInOut: "cubic-bezier(0.645, 0.045, 0.355, 1)",
  motionEaseOutBack: "cubic-bezier(0.12, 0.4, 0.29, 1.46)",
  motionEaseInBack: "cubic-bezier(0.71, -0.46, 0.88, 0.6)",
  motionEaseInQuint: "cubic-bezier(0.755, 0.05, 0.855, 0.06)",
  motionEaseOutQuint: "cubic-bezier(0.23, 1, 0.32, 1)",
  // Radius
  borderRadius: 6,
  // Size
  sizeUnit: 4,
  sizeStep: 4,
  sizePopupArrow: 16,
  // Control Base
  controlHeight: 32,
  // zIndex
  zIndexBase: 0,
  zIndexPopupBase: 1e3,
  // Image
  opacityImage: 1,
  // Wireframe
  wireframe: !1,
  // Motion
  motion: !0
}), M = Math.round;
function _e(t, e) {
  const n = t.replace(/^[^(]*\((.*)/, "$1").replace(/\).*/, "").match(/\d*\.?\d+%?/g) || [], o = n.map((r) => parseFloat(r));
  for (let r = 0; r < 3; r += 1)
    o[r] = e(o[r] || 0, n[r] || "", r);
  return n[3] ? o[3] = n[3].includes("%") ? o[3] / 100 : o[3] : o[3] = 1, o;
}
const it = (t, e, n) => n === 0 ? t : t / 100;
function N(t, e) {
  const n = e || 255;
  return t > n ? n : t < 0 ? 0 : t;
}
class B {
  constructor(e) {
    T(this, "isValid", !0), T(this, "r", 0), T(this, "g", 0), T(this, "b", 0), T(this, "a", 1), T(this, "_h", void 0), T(this, "_s", void 0), T(this, "_l", void 0), T(this, "_v", void 0), T(this, "_max", void 0), T(this, "_min", void 0), T(this, "_brightness", void 0);
    function n(o) {
      return o[0] in e && o[1] in e && o[2] in e;
    }
    if (e) if (typeof e == "string") {
      let r = function(i) {
        return o.startsWith(i);
      };
      const o = e.trim();
      /^#?[A-F\d]{3,8}$/i.test(o) ? this.fromHexString(o) : r("rgb") ? this.fromRgbString(o) : r("hsl") ? this.fromHslString(o) : (r("hsv") || r("hsb")) && this.fromHsvString(o);
    } else if (e instanceof B)
      this.r = e.r, this.g = e.g, this.b = e.b, this.a = e.a, this._h = e._h, this._s = e._s, this._l = e._l, this._v = e._v;
    else if (n("rgb"))
      this.r = N(e.r), this.g = N(e.g), this.b = N(e.b), this.a = typeof e.a == "number" ? N(e.a, 1) : 1;
    else if (n("hsl"))
      this.fromHsl(e);
    else if (n("hsv"))
      this.fromHsv(e);
    else
      throw new Error("@ant-design/fast-color: unsupported input " + JSON.stringify(e));
  }
  // ======================= Setter =======================
  setR(e) {
    return this._sc("r", e);
  }
  setG(e) {
    return this._sc("g", e);
  }
  setB(e) {
    return this._sc("b", e);
  }
  setA(e) {
    return this._sc("a", e, 1);
  }
  setHue(e) {
    const n = this.toHsv();
    return n.h = e, this._c(n);
  }
  // ======================= Getter =======================
  /**
   * Returns the perceived luminance of a color, from 0-1.
   * @see http://www.w3.org/TR/2008/REC-WCAG20-20081211/#relativeluminancedef
   */
  getLuminance() {
    function e(i) {
      const s = i / 255;
      return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    }
    const n = e(this.r), o = e(this.g), r = e(this.b);
    return 0.2126 * n + 0.7152 * o + 0.0722 * r;
  }
  getHue() {
    if (typeof this._h > "u") {
      const e = this.getMax() - this.getMin();
      e === 0 ? this._h = 0 : this._h = M(60 * (this.r === this.getMax() ? (this.g - this.b) / e + (this.g < this.b ? 6 : 0) : this.g === this.getMax() ? (this.b - this.r) / e + 2 : (this.r - this.g) / e + 4));
    }
    return this._h;
  }
  getSaturation() {
    if (typeof this._s > "u") {
      const e = this.getMax() - this.getMin();
      e === 0 ? this._s = 0 : this._s = e / this.getMax();
    }
    return this._s;
  }
  getLightness() {
    return typeof this._l > "u" && (this._l = (this.getMax() + this.getMin()) / 510), this._l;
  }
  getValue() {
    return typeof this._v > "u" && (this._v = this.getMax() / 255), this._v;
  }
  /**
   * Returns the perceived brightness of the color, from 0-255.
   * Note: this is not the b of HSB
   * @see http://www.w3.org/TR/AERT#color-contrast
   */
  getBrightness() {
    return typeof this._brightness > "u" && (this._brightness = (this.r * 299 + this.g * 587 + this.b * 114) / 1e3), this._brightness;
  }
  // ======================== Func ========================
  darken(e = 10) {
    const n = this.getHue(), o = this.getSaturation();
    let r = this.getLightness() - e / 100;
    return r < 0 && (r = 0), this._c({
      h: n,
      s: o,
      l: r,
      a: this.a
    });
  }
  lighten(e = 10) {
    const n = this.getHue(), o = this.getSaturation();
    let r = this.getLightness() + e / 100;
    return r > 1 && (r = 1), this._c({
      h: n,
      s: o,
      l: r,
      a: this.a
    });
  }
  /**
   * Mix the current color a given amount with another color, from 0 to 100.
   * 0 means no mixing (return current color).
   */
  mix(e, n = 50) {
    const o = this._c(e), r = n / 100, i = (a) => (o[a] - this[a]) * r + this[a], s = {
      r: M(i("r")),
      g: M(i("g")),
      b: M(i("b")),
      a: M(i("a") * 100) / 100
    };
    return this._c(s);
  }
  /**
   * Mix the color with pure white, from 0 to 100.
   * Providing 0 will do nothing, providing 100 will always return white.
   */
  tint(e = 10) {
    return this.mix({
      r: 255,
      g: 255,
      b: 255,
      a: 1
    }, e);
  }
  /**
   * Mix the color with pure black, from 0 to 100.
   * Providing 0 will do nothing, providing 100 will always return black.
   */
  shade(e = 10) {
    return this.mix({
      r: 0,
      g: 0,
      b: 0,
      a: 1
    }, e);
  }
  onBackground(e) {
    const n = this._c(e), o = this.a + n.a * (1 - this.a), r = (i) => M((this[i] * this.a + n[i] * n.a * (1 - this.a)) / o);
    return this._c({
      r: r("r"),
      g: r("g"),
      b: r("b"),
      a: o
    });
  }
  // ======================= Status =======================
  isDark() {
    return this.getBrightness() < 128;
  }
  isLight() {
    return this.getBrightness() >= 128;
  }
  // ======================== MISC ========================
  equals(e) {
    return this.r === e.r && this.g === e.g && this.b === e.b && this.a === e.a;
  }
  clone() {
    return this._c(this);
  }
  // ======================= Format =======================
  toHexString() {
    let e = "#";
    const n = (this.r || 0).toString(16);
    e += n.length === 2 ? n : "0" + n;
    const o = (this.g || 0).toString(16);
    e += o.length === 2 ? o : "0" + o;
    const r = (this.b || 0).toString(16);
    if (e += r.length === 2 ? r : "0" + r, typeof this.a == "number" && this.a >= 0 && this.a < 1) {
      const i = M(this.a * 255).toString(16);
      e += i.length === 2 ? i : "0" + i;
    }
    return e;
  }
  /** CSS support color pattern */
  toHsl() {
    return {
      h: this.getHue(),
      s: this.getSaturation(),
      l: this.getLightness(),
      a: this.a
    };
  }
  /** CSS support color pattern */
  toHslString() {
    const e = this.getHue(), n = M(this.getSaturation() * 100), o = M(this.getLightness() * 100);
    return this.a !== 1 ? `hsla(${e},${n}%,${o}%,${this.a})` : `hsl(${e},${n}%,${o}%)`;
  }
  /** Same as toHsb */
  toHsv() {
    return {
      h: this.getHue(),
      s: this.getSaturation(),
      v: this.getValue(),
      a: this.a
    };
  }
  toRgb() {
    return {
      r: this.r,
      g: this.g,
      b: this.b,
      a: this.a
    };
  }
  toRgbString() {
    return this.a !== 1 ? `rgba(${this.r},${this.g},${this.b},${this.a})` : `rgb(${this.r},${this.g},${this.b})`;
  }
  toString() {
    return this.toRgbString();
  }
  // ====================== Privates ======================
  /** Return a new FastColor object with one channel changed */
  _sc(e, n, o) {
    const r = this.clone();
    return r[e] = N(n, o), r;
  }
  _c(e) {
    return new this.constructor(e);
  }
  getMax() {
    return typeof this._max > "u" && (this._max = Math.max(this.r, this.g, this.b)), this._max;
  }
  getMin() {
    return typeof this._min > "u" && (this._min = Math.min(this.r, this.g, this.b)), this._min;
  }
  fromHexString(e) {
    const n = e.replace("#", "");
    function o(r, i) {
      return parseInt(n[r] + n[i || r], 16);
    }
    n.length < 6 ? (this.r = o(0), this.g = o(1), this.b = o(2), this.a = n[3] ? o(3) / 255 : 1) : (this.r = o(0, 1), this.g = o(2, 3), this.b = o(4, 5), this.a = n[6] ? o(6, 7) / 255 : 1);
  }
  fromHsl({
    h: e,
    s: n,
    l: o,
    a: r
  }) {
    if (this._h = e % 360, this._s = n, this._l = o, this.a = typeof r == "number" ? r : 1, n <= 0) {
      const d = M(o * 255);
      this.r = d, this.g = d, this.b = d;
    }
    let i = 0, s = 0, a = 0;
    const l = e / 60, c = (1 - Math.abs(2 * o - 1)) * n, u = c * (1 - Math.abs(l % 2 - 1));
    l >= 0 && l < 1 ? (i = c, s = u) : l >= 1 && l < 2 ? (i = u, s = c) : l >= 2 && l < 3 ? (s = c, a = u) : l >= 3 && l < 4 ? (s = u, a = c) : l >= 4 && l < 5 ? (i = u, a = c) : l >= 5 && l < 6 && (i = c, a = u);
    const f = o - c / 2;
    this.r = M((i + f) * 255), this.g = M((s + f) * 255), this.b = M((a + f) * 255);
  }
  fromHsv({
    h: e,
    s: n,
    v: o,
    a: r
  }) {
    this._h = e % 360, this._s = n, this._v = o, this.a = typeof r == "number" ? r : 1;
    const i = M(o * 255);
    if (this.r = i, this.g = i, this.b = i, n <= 0)
      return;
    const s = e / 60, a = Math.floor(s), l = s - a, c = M(o * (1 - n) * 255), u = M(o * (1 - n * l) * 255), f = M(o * (1 - n * (1 - l)) * 255);
    switch (a) {
      case 0:
        this.g = f, this.b = c;
        break;
      case 1:
        this.r = u, this.b = c;
        break;
      case 2:
        this.r = c, this.b = f;
        break;
      case 3:
        this.r = c, this.g = u;
        break;
      case 4:
        this.r = f, this.g = c;
        break;
      case 5:
      default:
        this.g = c, this.b = u;
        break;
    }
  }
  fromHsvString(e) {
    const n = _e(e, it);
    this.fromHsv({
      h: n[0],
      s: n[1],
      v: n[2],
      a: n[3]
    });
  }
  fromHslString(e) {
    const n = _e(e, it);
    this.fromHsl({
      h: n[0],
      s: n[1],
      l: n[2],
      a: n[3]
    });
  }
  fromRgbString(e) {
    const n = _e(e, (o, r) => (
      // Convert percentage to number. e.g. 50% -> 128
      r.includes("%") ? M(o / 100 * 255) : o
    ));
    this.r = n[0], this.g = n[1], this.b = n[2], this.a = n[3];
  }
}
function Ce(t) {
  return t >= 0 && t <= 255;
}
function K(t, e) {
  const {
    r: n,
    g: o,
    b: r,
    a: i
  } = new B(t).toRgb();
  if (i < 1)
    return t;
  const {
    r: s,
    g: a,
    b: l
  } = new B(e).toRgb();
  for (let c = 0.01; c <= 1; c += 0.01) {
    const u = Math.round((n - s * (1 - c)) / c), f = Math.round((o - a * (1 - c)) / c), d = Math.round((r - l * (1 - c)) / c);
    if (Ce(u) && Ce(f) && Ce(d))
      return new B({
        r: u,
        g: f,
        b: d,
        a: Math.round(c * 100) / 100
      }).toRgbString();
  }
  return new B({
    r: n,
    g: o,
    b: r,
    a: 1
  }).toRgbString();
}
var ln = function(t, e) {
  var n = {};
  for (var o in t) Object.prototype.hasOwnProperty.call(t, o) && e.indexOf(o) < 0 && (n[o] = t[o]);
  if (t != null && typeof Object.getOwnPropertySymbols == "function") for (var r = 0, o = Object.getOwnPropertySymbols(t); r < o.length; r++)
    e.indexOf(o[r]) < 0 && Object.prototype.propertyIsEnumerable.call(t, o[r]) && (n[o[r]] = t[o[r]]);
  return n;
};
function cn(t) {
  const {
    override: e
  } = t, n = ln(t, ["override"]), o = Object.assign({}, e);
  Object.keys(an).forEach((d) => {
    delete o[d];
  });
  const r = Object.assign(Object.assign({}, n), o), i = 480, s = 576, a = 768, l = 992, c = 1200, u = 1600;
  if (r.motion === !1) {
    const d = "0s";
    r.motionDurationFast = d, r.motionDurationMid = d, r.motionDurationSlow = d;
  }
  return Object.assign(Object.assign(Object.assign({}, r), {
    // ============== Background ============== //
    colorFillContent: r.colorFillSecondary,
    colorFillContentHover: r.colorFill,
    colorFillAlter: r.colorFillQuaternary,
    colorBgContainerDisabled: r.colorFillTertiary,
    // ============== Split ============== //
    colorBorderBg: r.colorBgContainer,
    colorSplit: K(r.colorBorderSecondary, r.colorBgContainer),
    // ============== Text ============== //
    colorTextPlaceholder: r.colorTextQuaternary,
    colorTextDisabled: r.colorTextQuaternary,
    colorTextHeading: r.colorText,
    colorTextLabel: r.colorTextSecondary,
    colorTextDescription: r.colorTextTertiary,
    colorTextLightSolid: r.colorWhite,
    colorHighlight: r.colorError,
    colorBgTextHover: r.colorFillSecondary,
    colorBgTextActive: r.colorFill,
    colorIcon: r.colorTextTertiary,
    colorIconHover: r.colorText,
    colorErrorOutline: K(r.colorErrorBg, r.colorBgContainer),
    colorWarningOutline: K(r.colorWarningBg, r.colorBgContainer),
    // Font
    fontSizeIcon: r.fontSizeSM,
    // Line
    lineWidthFocus: r.lineWidth * 3,
    // Control
    lineWidth: r.lineWidth,
    controlOutlineWidth: r.lineWidth * 2,
    // Checkbox size and expand icon size
    controlInteractiveSize: r.controlHeight / 2,
    controlItemBgHover: r.colorFillTertiary,
    controlItemBgActive: r.colorPrimaryBg,
    controlItemBgActiveHover: r.colorPrimaryBgHover,
    controlItemBgActiveDisabled: r.colorFill,
    controlTmpOutline: r.colorFillQuaternary,
    controlOutline: K(r.colorPrimaryBg, r.colorBgContainer),
    lineType: r.lineType,
    borderRadius: r.borderRadius,
    borderRadiusXS: r.borderRadiusXS,
    borderRadiusSM: r.borderRadiusSM,
    borderRadiusLG: r.borderRadiusLG,
    fontWeightStrong: 600,
    opacityLoading: 0.65,
    linkDecoration: "none",
    linkHoverDecoration: "none",
    linkFocusDecoration: "none",
    controlPaddingHorizontal: 12,
    controlPaddingHorizontalSM: 8,
    paddingXXS: r.sizeXXS,
    paddingXS: r.sizeXS,
    paddingSM: r.sizeSM,
    padding: r.size,
    paddingMD: r.sizeMD,
    paddingLG: r.sizeLG,
    paddingXL: r.sizeXL,
    paddingContentHorizontalLG: r.sizeLG,
    paddingContentVerticalLG: r.sizeMS,
    paddingContentHorizontal: r.sizeMS,
    paddingContentVertical: r.sizeSM,
    paddingContentHorizontalSM: r.size,
    paddingContentVerticalSM: r.sizeXS,
    marginXXS: r.sizeXXS,
    marginXS: r.sizeXS,
    marginSM: r.sizeSM,
    margin: r.size,
    marginMD: r.sizeMD,
    marginLG: r.sizeLG,
    marginXL: r.sizeXL,
    marginXXL: r.sizeXXL,
    boxShadow: `
      0 6px 16px 0 rgba(0, 0, 0, 0.08),
      0 3px 6px -4px rgba(0, 0, 0, 0.12),
      0 9px 28px 8px rgba(0, 0, 0, 0.05)
    `,
    boxShadowSecondary: `
      0 6px 16px 0 rgba(0, 0, 0, 0.08),
      0 3px 6px -4px rgba(0, 0, 0, 0.12),
      0 9px 28px 8px rgba(0, 0, 0, 0.05)
    `,
    boxShadowTertiary: `
      0 1px 2px 0 rgba(0, 0, 0, 0.03),
      0 1px 6px -1px rgba(0, 0, 0, 0.02),
      0 2px 4px 0 rgba(0, 0, 0, 0.02)
    `,
    screenXS: i,
    screenXSMin: i,
    screenXSMax: s - 1,
    screenSM: s,
    screenSMMin: s,
    screenSMMax: a - 1,
    screenMD: a,
    screenMDMin: a,
    screenMDMax: l - 1,
    screenLG: l,
    screenLGMin: l,
    screenLGMax: c - 1,
    screenXL: c,
    screenXLMin: c,
    screenXLMax: u - 1,
    screenXXL: u,
    screenXXLMin: u,
    boxShadowPopoverArrow: "2px 2px 5px rgba(0, 0, 0, 0.05)",
    boxShadowCard: `
      0 1px 2px -2px ${new B("rgba(0, 0, 0, 0.16)").toRgbString()},
      0 3px 6px 0 ${new B("rgba(0, 0, 0, 0.12)").toRgbString()},
      0 5px 12px 4px ${new B("rgba(0, 0, 0, 0.09)").toRgbString()}
    `,
    boxShadowDrawerRight: `
      -6px 0 16px 0 rgba(0, 0, 0, 0.08),
      -3px 0 6px -4px rgba(0, 0, 0, 0.12),
      -9px 0 28px 8px rgba(0, 0, 0, 0.05)
    `,
    boxShadowDrawerLeft: `
      6px 0 16px 0 rgba(0, 0, 0, 0.08),
      3px 0 6px -4px rgba(0, 0, 0, 0.12),
      9px 0 28px 8px rgba(0, 0, 0, 0.05)
    `,
    boxShadowDrawerUp: `
      0 6px 16px 0 rgba(0, 0, 0, 0.08),
      0 3px 6px -4px rgba(0, 0, 0, 0.12),
      0 9px 28px 8px rgba(0, 0, 0, 0.05)
    `,
    boxShadowDrawerDown: `
      0 -6px 16px 0 rgba(0, 0, 0, 0.08),
      0 -3px 6px -4px rgba(0, 0, 0, 0.12),
      0 -9px 28px 8px rgba(0, 0, 0, 0.05)
    `,
    boxShadowTabsOverflowLeft: "inset 10px 0 8px -8px rgba(0, 0, 0, 0.08)",
    boxShadowTabsOverflowRight: "inset -10px 0 8px -8px rgba(0, 0, 0, 0.08)",
    boxShadowTabsOverflowTop: "inset 0 10px 8px -8px rgba(0, 0, 0, 0.08)",
    boxShadowTabsOverflowBottom: "inset 0 -10px 8px -8px rgba(0, 0, 0, 0.08)"
  }), o);
}
const un = {
  lineHeight: !0,
  lineHeightSM: !0,
  lineHeightLG: !0,
  lineHeightHeading1: !0,
  lineHeightHeading2: !0,
  lineHeightHeading3: !0,
  lineHeightHeading4: !0,
  lineHeightHeading5: !0,
  opacityLoading: !0,
  fontWeightStrong: !0,
  zIndexPopupBase: !0,
  zIndexBase: !0,
  opacityImage: !0
}, fn = {
  size: !0,
  sizeSM: !0,
  sizeLG: !0,
  sizeMD: !0,
  sizeXS: !0,
  sizeXXS: !0,
  sizeMS: !0,
  sizeXL: !0,
  sizeXXL: !0,
  sizeUnit: !0,
  sizeStep: !0,
  motionBase: !0,
  motionUnit: !0
}, dn = Wt(Oe.defaultAlgorithm), hn = {
  screenXS: !0,
  screenXSMin: !0,
  screenXSMax: !0,
  screenSM: !0,
  screenSMMin: !0,
  screenSMMax: !0,
  screenMD: !0,
  screenMDMin: !0,
  screenMDMax: !0,
  screenLG: !0,
  screenLGMin: !0,
  screenLGMax: !0,
  screenXL: !0,
  screenXLMin: !0,
  screenXLMax: !0,
  screenXXL: !0,
  screenXXLMin: !0
}, St = (t, e, n) => {
  const o = n.getDerivativeToken(t), {
    override: r,
    ...i
  } = e;
  let s = {
    ...o,
    override: r
  };
  return s = cn(s), i && Object.entries(i).forEach(([a, l]) => {
    const {
      theme: c,
      ...u
    } = l;
    let f = u;
    c && (f = St({
      ...s,
      ...u
    }, {
      override: u
    }, c)), s[a] = f;
  }), s;
};
function gn() {
  const {
    token: t,
    hashed: e,
    theme: n = dn,
    override: o,
    cssVar: r
  } = _.useContext(Oe._internalContext), [i, s, a] = qt(n, [Oe.defaultSeed, t], {
    salt: `${Rr}-${e || ""}`,
    override: o,
    getComputedToken: St,
    cssVar: r && {
      prefix: r.prefix,
      key: r.key,
      unitless: un,
      ignore: fn,
      preserve: hn
    }
  });
  return [n, a, e ? s : "", i, r];
}
const {
  genStyleHooks: pn
} = on({
  usePrefix: () => {
    const {
      getPrefixCls: t,
      iconPrefixCls: e
    } = re();
    return {
      iconPrefixCls: e,
      rootPrefixCls: t()
    };
  },
  useToken: () => {
    const [t, e, n, o, r] = gn();
    return {
      theme: t,
      realToken: e,
      hashId: n,
      token: o,
      cssVar: r
    };
  },
  useCSP: () => {
    const {
      csp: t
    } = re();
    return t ?? {};
  },
  layer: {
    name: "antdx",
    dependencies: ["antd"]
  }
}), mn = (t) => {
  const {
    componentCls: e,
    calc: n
  } = t;
  return {
    [e]: {
      [`${e}-list`]: {
        display: "inline-flex",
        flexDirection: "row",
        gap: t.paddingXS,
        color: t.colorTextDescription,
        "&-item, &-sub-item": {
          cursor: "pointer",
          padding: t.paddingXXS,
          borderRadius: t.borderRadius,
          height: t.controlHeightSM,
          width: t.controlHeightSM,
          boxSizing: "border-box",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          "&-icon": {
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: t.fontSize,
            width: "100%",
            height: "100%"
          },
          "&:hover": {
            background: t.colorBgTextHover
          }
        }
      },
      "& .border": {
        padding: `${t.paddingXS} ${t.paddingSM}`,
        gap: t.paddingSM,
        borderRadius: n(t.borderRadiusLG).mul(1.5).equal(),
        backgroundColor: t.colorBorderSecondary,
        color: t.colorTextSecondary,
        [`${e}-list-item, ${e}-list-sub-item`]: {
          padding: 0,
          lineHeight: t.lineHeight,
          "&-icon": {
            fontSize: t.fontSizeLG
          },
          "&:hover": {
            opacity: 0.8
          }
        }
      },
      "& .block": {
        display: "flex"
      }
    }
  };
}, bn = () => ({}), yn = pn("Actions", (t) => {
  const e = Re(t, {});
  return [mn(e)];
}, bn), vn = (t) => {
  const {
    prefixCls: e,
    rootClassName: n = {},
    style: o = {},
    variant: r = "borderless",
    block: i = !1,
    onClick: s,
    items: a = [],
    ...l
  } = t, {
    getPrefixCls: c
  } = re(), u = c("actions", e), f = Hr("actions"), [d, p, y] = yn(u), x = J(u, f.className, n, y, p), g = {
    ...f.style,
    ...o
  }, b = (h, v, m) => v ? /* @__PURE__ */ _.createElement(Nt, te({}, m, {
    title: v
  }), h) : h, C = (h, v, m) => {
    if (v.onItemClick) {
      v.onItemClick(v);
      return;
    }
    s == null || s({
      key: h,
      item: v,
      keyPath: [h],
      domEvent: m
    });
  }, E = (h) => {
    const {
      icon: v,
      label: m,
      key: w
    } = h;
    return /* @__PURE__ */ _.createElement("div", {
      className: J(`${u}-list-item`),
      onClick: (O) => C(w, h, O),
      key: w
    }, b(/* @__PURE__ */ _.createElement("div", {
      className: `${u}-list-item-icon`
    }, v), m));
  };
  return d(/* @__PURE__ */ _.createElement("div", te({
    className: x
  }, l, {
    style: g
  }), /* @__PURE__ */ _.createElement("div", {
    className: J(`${u}-list`, r, i)
  }, a.map((h) => "children" in h ? /* @__PURE__ */ _.createElement(zr, {
    key: h.key,
    item: h,
    prefixCls: u,
    onClick: s
  }) : E(h)))));
}, xn = ["animationIterationCount", "borderImageOutset", "borderImageSlice", "borderImageWidth", "boxFlex", "boxFlexGroup", "boxOrdinalGroup", "columnCount", "columns", "flex", "flexGrow", "flexPositive", "flexShrink", "flexNegative", "flexOrder", "gridArea", "gridColumn", "gridColumnEnd", "gridColumnStart", "gridRow", "gridRowEnd", "gridRowStart", "lineClamp", "lineHeight", "opacity", "order", "orphans", "tabSize", "widows", "zIndex", "zoom", "fontWeight", "letterSpacing", "lineHeight"];
function Sn(t) {
  return t ? Object.keys(t).reduce((e, n) => {
    const o = t[n];
    return e[n] = _n(n, o), e;
  }, {}) : {};
}
function _n(t, e) {
  return typeof e == "number" && !xn.includes(t) ? e + "px" : e;
}
function Ie(t) {
  const e = [], n = t.cloneNode(!1);
  if (t._reactElement) {
    const r = _.Children.toArray(t._reactElement.props.children).map((i) => {
      if (_.isValidElement(i) && i.props.__slot__) {
        const {
          portals: s,
          clonedElement: a
        } = Ie(i.props.el);
        return _.cloneElement(i, {
          ...i.props,
          el: a,
          children: [..._.Children.toArray(i.props.children), ...s]
        });
      }
      return null;
    });
    return r.originalChildren = t._reactElement.props.children, e.push(we(_.cloneElement(t._reactElement, {
      ...t._reactElement.props,
      children: r
    }), n)), {
      clonedElement: n,
      portals: e
    };
  }
  Object.keys(t.getEventListeners()).forEach((r) => {
    t.getEventListeners(r).forEach(({
      listener: s,
      type: a,
      useCapture: l
    }) => {
      n.addEventListener(a, s, l);
    });
  });
  const o = Array.from(t.childNodes);
  for (let r = 0; r < o.length; r++) {
    const i = o[r];
    if (i.nodeType === 1) {
      const {
        clonedElement: s,
        portals: a
      } = Ie(i);
      e.push(...a), n.appendChild(s);
    } else i.nodeType === 3 && n.appendChild(i.cloneNode());
  }
  return {
    clonedElement: n,
    portals: e
  };
}
function Cn(t, e) {
  t && (typeof t == "function" ? t(e) : t.current = e);
}
const st = kt(({
  slot: t,
  clone: e,
  className: n,
  style: o,
  observeAttributes: r
}, i) => {
  const s = Rt(), [a, l] = Lt([]), {
    forceClone: c
  } = Xt(), u = c ? !0 : e;
  return At(() => {
    var x;
    if (!s.current || !t)
      return;
    let f = t;
    function d() {
      let g = f;
      if (f.tagName.toLowerCase() === "svelte-slot" && f.children.length === 1 && f.children[0] && (g = f.children[0], g.tagName.toLowerCase() === "react-portal-target" && g.children[0] && (g = g.children[0])), Cn(i, g), n && g.classList.add(...n.split(" ")), o) {
        const b = Sn(o);
        Object.keys(b).forEach((C) => {
          g.style[C] = b[C];
        });
      }
    }
    let p = null, y = null;
    if (u && window.MutationObserver) {
      let g = function() {
        var h, v, m;
        (h = s.current) != null && h.contains(f) && ((v = s.current) == null || v.removeChild(f));
        const {
          portals: C,
          clonedElement: E
        } = Ie(t);
        f = E, l(C), f.style.display = "contents", y && clearTimeout(y), y = setTimeout(() => {
          d();
        }, 50), (m = s.current) == null || m.appendChild(f);
      };
      g();
      const b = sr(() => {
        g(), p == null || p.disconnect(), p == null || p.observe(t, {
          childList: !0,
          subtree: !0,
          attributes: r
        });
      }, 50);
      p = new window.MutationObserver(b), p.observe(t, {
        attributes: !0,
        childList: !0,
        subtree: !0
      });
    } else
      f.style.display = "contents", d(), (x = s.current) == null || x.appendChild(f);
    return () => {
      var g, b;
      f.style.display = "", (g = s.current) != null && g.contains(f) && ((b = s.current) == null || b.removeChild(f)), p == null || p.disconnect();
    };
  }, [t, u, n, o, i, r, c]), _.createElement("react-child", {
    ref: s,
    style: {
      display: "contents"
    }
  }, ...a);
}), wn = ({
  children: t,
  ...e
}) => /* @__PURE__ */ z.jsx(z.Fragment, {
  children: t(e)
});
function Tn(t) {
  return _.createElement(wn, {
    children: t
  });
}
function _t(t, e, n) {
  const o = t.filter(Boolean);
  if (o.length !== 0)
    return o.map((r, i) => {
      var c;
      if (typeof r != "object")
        return e != null && e.fallback ? e.fallback(r) : r;
      const s = {
        ...r.props,
        key: ((c = r.props) == null ? void 0 : c.key) ?? (n ? `${n}-${i}` : `${i}`)
      };
      let a = s;
      Object.keys(r.slots).forEach((u) => {
        if (!r.slots[u] || !(r.slots[u] instanceof Element) && !r.slots[u].el)
          return;
        const f = u.split(".");
        f.forEach((b, C) => {
          a[b] || (a[b] = {}), C !== f.length - 1 && (a = s[b]);
        });
        const d = r.slots[u];
        let p, y, x = (e == null ? void 0 : e.clone) ?? !1, g = e == null ? void 0 : e.forceClone;
        d instanceof Element ? p = d : (p = d.el, y = d.callback, x = d.clone ?? x, g = d.forceClone ?? g), g = g ?? !!y, a[f[f.length - 1]] = p ? y ? (...b) => (y(f[f.length - 1], b), /* @__PURE__ */ z.jsx(De, {
          ...r.ctx,
          params: b,
          forceClone: g,
          children: /* @__PURE__ */ z.jsx(st, {
            slot: p,
            clone: x
          })
        })) : Tn((b) => /* @__PURE__ */ z.jsx(De, {
          ...r.ctx,
          forceClone: g,
          children: /* @__PURE__ */ z.jsx(st, {
            ...b,
            slot: p,
            clone: x
          })
        })) : a[f[f.length - 1]], a = s;
      });
      const l = (e == null ? void 0 : e.children) || "children";
      return r[l] ? s[l] = _t(r[l], e, `${i}`) : e != null && e.children && (s[l] = void 0, Reflect.deleteProperty(s, l)), s;
    });
}
const {
  useItems: On,
  withItemsContextProvider: Mn,
  ItemHandler: In
} = $t("antdx-actions-items"), jn = kr(Mn(["default", "items"], ({
  children: t,
  items: e,
  className: n,
  ...o
}) => {
  const {
    items: r
  } = On(), i = r.items.length > 0 ? r.items : r.default;
  return /* @__PURE__ */ z.jsxs(z.Fragment, {
    children: [/* @__PURE__ */ z.jsx("div", {
      style: {
        display: "none"
      },
      children: t
    }), /* @__PURE__ */ z.jsx(vn, {
      ...o,
      rootClassName: J(n, o.rootClassName),
      items: Ht(() => e || _t(i, {
        clone: !0
      }) || [], [e, i])
    })]
  });
}));
export {
  jn as Actions,
  jn as default
};
