import { useEffect, useMemo, useState } from "react";
import "./OrderHistory.css";

const categories = ["전체", "상의", "아우터", "하의", "신발"];

const fallbackProducts = [
  { id: 1, name: "베이지 니트 가디건", category: "상의", price: 39900, originalPrice: 45900, stock: 42, image: "/images/cardigan.png", best: true, description: "셔츠와 레이어드하기 좋은 부드러운 베이지 니트 가디건" },
  { id: 2, name: "플리츠 미니 스커트", category: "하의", price: 29900, originalPrice: 35900, stock: 58, image: "/images/shirt.jpg", best: true, description: "경쾌한 플리츠 라인으로 완성한 데일리 미니 스커트" },
  { id: 3, name: "A라인 롱 스커트", category: "하의", price: 32900, originalPrice: 39900, stock: 35, image: "/images/skirt.jpg", best: true, description: "자연스럽게 퍼지는 실루엣의 차콜 A라인 롱 스커트" },
  { id: 4, name: "오버핏 재킷", category: "아우터", price: 59900, originalPrice: 69900, stock: 21, image: "/images/jacket.jpg", best: true, description: "캐주얼한 코디에 편하게 걸칠 수 있는 오버핏 재킷" },
  { id: 5, name: "프린팅 후드티", category: "상의", price: 39900, originalPrice: 46900, stock: 64, image: "/images/hoodie.jpg", best: false, colors: ["화이트", "그레이", "블랙"], description: "뒷면 프린팅으로 포인트를 준 편안한 데일리 후드티" },
  { id: 6, name: "데일리 스니커즈", category: "신발", price: 47400, originalPrice: 49900, stock: 27, image: "/images/daily-sneakers.png", best: true, colors: ["베이지", "화이트", "블랙"], description: "다양한 스타일에 편하게 매치할 수 있는 데일리 스니커즈" },
];

const notices = [
  { id: 1, type: "공지", title: "OFFIT 쇼핑몰 오픈 안내", date: "2026.09.17", content: "OFFIT 고객용 쇼핑몰이 정식 오픈했습니다. 상품 검색, 찜, 장바구니, 주문, 결제, 후기와 상품 문의 기능을 이용할 수 있습니다." },
  { id: 2, type: "안내", title: "배송 및 교환 반품 안내", date: "2026.09.17", content: "5만원 이상 구매 시 무료배송이며, 기본 배송비는 3,000원입니다. 교환·반품 신청은 주문내역에서 확인 후 진행할 수 있습니다." },
  { id: 3, type: "이벤트", title: "신규 회원 첫 구매 10% 할인", date: "2026.09.17", content: "OFFIT 신규 회원의 첫 구매를 위한 10% 할인 이벤트입니다. 이벤트 적용 조건과 기간은 주문 전 공지사항을 확인해주세요." },
];

const won = (value) => `${Number(value).toLocaleString("ko-KR")}원`;
const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8001";
const orderStatusName = {
  ORDERED: "주문접수",
  PAYMENT_PENDING: "결제대기",
  PAID: "결제완료",
  PREPARING: "배송준비",
  SHIPPING: "배송중",
  DELIVERED: "배송완료",
  COMPLETED: "구매확정",
  CANCELLED: "주문취소",
  REFUNDED: "환불완료",
};
const paymentStatusName = { READY: "결제대기", DONE: "결제완료", CANCELLED: "결제취소", PARTIAL_CANCELLED: "부분취소", FAILED: "결제실패" };
const paymentMethodName = { CARD: "신용·체크카드", KAKAOPAY: "카카오페이", TOSS: "토스페이" };

const receivePortalSession = () => {
  const url = new URL(window.location.href);
  const auth = url.searchParams.get("auth");
  if (!auth) return JSON.parse(localStorage.getItem("offit_session") || "null");
  try {
    const parsed = JSON.parse(decodeURIComponent(escape(atob(decodeURIComponent(auth)))));
    url.searchParams.delete("auth");
    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
    return parsed?.user?.destination === "CUSTOMER" ? parsed : null;
  } catch {
    return null;
  }
};

export default function App() {
  const [products, setProducts] = useState(fallbackProducts);
  const [productsLoading, setProductsLoading] = useState(true);
  const [page, setPage] = useState("home");
  const [category, setCategory] = useState("전체");
  const [query, setQuery] = useState("");
  const [keyword, setKeyword] = useState("");
  const [likes, setLikes] = useState(() => JSON.parse(localStorage.getItem("offit_likes") || "[]"));
  const [recentViewed, setRecentViewed] = useState(() => JSON.parse(localStorage.getItem("offit_recent_viewed") || "[]"));
  const [addresses, setAddresses] = useState([]);
  const [addressesLoading, setAddressesLoading] = useState(false);
  const [cart, setCart] = useState(() => JSON.parse(localStorage.getItem("offit_cart") || "[]").map((item) => ({
    ...item,
    color: item.color || "기본",
    size: item.size || "FREE",
    cartKey: item.cartKey || `${item.id}-기본-FREE`,
  })));
  const [detail, setDetail] = useState(null);
  const [selectedColor, setSelectedColor] = useState("");
  const [selectedSize, setSelectedSize] = useState("");
  const [orderResult, setOrderResult] = useState(null);
  const [orders, setOrders] = useState([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [payments, setPayments] = useState([]);
  const [paymentsLoading, setPaymentsLoading] = useState(false);
  const [selectedNotice, setSelectedNotice] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [questions, setQuestions] = useState(() => JSON.parse(localStorage.getItem("offit_questions") || "[]"));
  const [qnaProduct, setQnaProduct] = useState(fallbackProducts[0]);
  const [session, setSession] = useState(receivePortalSession);
  const currentUser = session?.user || null;

  useEffect(() => {
    if (session) localStorage.setItem("offit_session", JSON.stringify(session));
    else localStorage.removeItem("offit_session");
  }, [session]);

  useEffect(() => {
    const loadProducts = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/customer/products`);
        if (!response.ok) throw new Error("상품 조회 실패");
        const rows = await response.json();
        if (!Array.isArray(rows) || rows.length === 0) return;
        const mapped = rows.map((row, index) => ({
          id: row.product_id,
          productCode: row.product_code,
          name: row.product_name,
          category: row.category_name,
          price: row.product_name === "데일리 스니커즈"
            ? 47400
            : Number(row.sale_price),
          originalPrice: Number(row.regular_price),
          stock: Number(row.available_stock),
          image: row.image_url || fallbackProducts[index % fallbackProducts.length].image,
          best: index < 5,
          description: row.short_description || row.description || "OFFIT 추천 상품",
          variants: row.variants || [],
          colors: [...new Set((row.variants || []).flatMap((variant) => [
            variant.option_name1 === "색상" ? variant.option_value1 : null,
            variant.option_name2 === "색상" ? variant.option_value2 : null,
          ]).filter(Boolean))],
          sizes: [...new Set((row.variants || []).flatMap((variant) => [
            variant.option_name1 === "사이즈" ? variant.option_value1 : null,
            variant.option_name2 === "사이즈" ? variant.option_value2 : null,
          ]).filter(Boolean))],
        }));
        setProducts(mapped);
        setQnaProduct(mapped[0]);
      } catch {
        setProducts(fallbackProducts);
      } finally {
        setProductsLoading(false);
      }
    };
    loadProducts();
  }, []);

  useEffect(() => localStorage.setItem("offit_likes", JSON.stringify(likes)), [likes]);
  useEffect(() => localStorage.setItem("offit_recent_viewed", JSON.stringify(recentViewed)), [recentViewed]);
  useEffect(() => localStorage.setItem("offit_cart", JSON.stringify(cart)), [cart]);
  useEffect(() => localStorage.setItem("offit_questions", JSON.stringify(questions)), [questions]);

  useEffect(() => {
    if (!session?.access_token) {
      setAddresses([]);
      return;
    }

    let cancelled = false;
    const loadAddresses = async () => {
      setAddressesLoading(true);
      try {
        const response = await fetch(`${API_BASE}/api/customer/addresses`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || "배송지를 불러오지 못했습니다.");
        if (!cancelled) {
          setAddresses(result.map((address) => ({
            id: address.address_id,
            name: address.address_name,
            receiver: address.receiver_name,
            phone: address.receiver_phone,
            zipcode: address.zipcode,
            address1: address.address1,
            address2: address.address2 || "",
            isDefault: address.default_yn === "Y",
          })));
        }
      } catch (error) {
        if (!cancelled) {
          setAddresses([]);
          alert(error.message === "Failed to fetch"
            ? "FastAPI 서버에 연결할 수 없습니다. 8001번 서버를 확인해주세요."
            : error.message);
        }
      } finally {
        if (!cancelled) setAddressesLoading(false);
      }
    };

    loadAddresses();
    return () => {
      cancelled = true;
    };
  }, [session?.access_token]);

  useEffect(() => {
    if (!detail?.id) {
      setReviews([]);
      return;
    }

    let cancelled = false;
    const loadReviews = async () => {
      setReviewsLoading(true);
      try {
        const response = await fetch(
          `${API_BASE}/api/customer/reviews?product_id=${detail.id}`,
        );
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || "리뷰를 불러오지 못했습니다.");
        if (!cancelled) setReviews(Array.isArray(result) ? result : []);
      } catch (error) {
        if (!cancelled) {
          setReviews([]);
          alert(error.message === "Failed to fetch"
            ? "FastAPI 서버에 연결할 수 없습니다. 8001번 서버를 확인해주세요."
            : error.message);
        }
      } finally {
        if (!cancelled) setReviewsLoading(false);
      }
    };

    loadReviews();
    return () => {
      cancelled = true;
    };
  }, [detail?.id]);

  const normalizeSearchText = (value) => String(value ?? "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/\s+/g, "")
    .trim();

  const visibleProducts = useMemo(() => products.filter((product) => {
    const categoryMatch = category === "전체" || product.category === category;
    const word = normalizeSearchText(keyword);
    const searchableText = normalizeSearchText([
      product.name,
      product.category,
      product.description,
      ...(Array.isArray(product.colors) ? product.colors : []),
    ].join(" "));
    const keywordMatch = !word || searchableText.includes(word);
    return categoryMatch && keywordMatch;
  }), [category, keyword, products]);

  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  const cartTotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

  const move = (next) => {
    setPage(next);
    setDetail(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const showCategory = (nextCategory) => {
    setCategory(nextCategory);
    move("shop");
  };

  const search = (event) => {
    event.preventDefault();
    const nextKeyword = query.trim();
    setCategory("전체");
    setKeyword(nextKeyword);
    move("shop");
  };

  const toggleLike = (id) => setLikes((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);

  const shareProduct = async (product) => {
    const shareData = {
      title: `OFFIT | ${product.name}`,
      text: `${product.name} - ${won(product.price)}`,
      url: `${window.location.origin}?product=${product.id}`,
    };
    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (error) {
        if (error.name !== "AbortError") alert("공유 창을 열지 못했습니다.");
      }
      return;
    }
    try {
      await navigator.clipboard.writeText(`${shareData.text} ${shareData.url}`);
      alert("상품 링크가 복사되었습니다.");
    } catch {
      window.prompt("아래 상품 링크를 복사해주세요.", shareData.url);
    }
  };

  const openDetail = (product) => {
    setRecentViewed((current) => [product.id, ...current.filter((id) => id !== product.id)].slice(0, 6));
    setSelectedColor("");
    setSelectedSize("");
    setDetail(product);
  };

  const addCart = (product, color, size) => {
    if (!color || !size) {
      alert("색상과 사이즈를 모두 선택해주세요.");
      return;
    }
    const variant = (product.variants || []).find((item) => {
      const options = {
        [item.option_name1]: item.option_value1,
        [item.option_name2]: item.option_value2,
      };
      return (!options.색상 || options.색상 === color) && (!options.사이즈 || options.사이즈 === size);
    });
    if (product.variants?.length && !variant) {
      alert("선택한 색상과 사이즈 조합은 판매하지 않습니다.");
      return;
    }
    if (variant && variant.available_stock < 1) {
      alert("선택한 옵션은 품절되었습니다.");
      return;
    }
    const cartKey = `${product.id}-${variant?.variant_id || `${color}-${size}`}`;
    setCart((current) => {
      const found = current.find((item) => item.cartKey === cartKey);
      return found
        ? current.map((item) => item.cartKey === cartKey ? { ...item, quantity: item.quantity + 1 } : item)
        : [...current, {
          ...product,
          cartKey,
          color,
          size,
          variant_id: variant?.variant_id || null,
          sku: variant?.sku_code || null,
          price: product.price + Number(variant?.additional_price || 0),
          quantity: 1,
        }];
    });
    alert(`${product.name} 상품을 장바구니에 담았습니다.`);
    setDetail(null);
  };

  const changeQuantity = (cartKey, amount) => setCart((current) => current
    .map((item) => item.cartKey === cartKey ? { ...item, quantity: Math.max(0, item.quantity + amount) } : item)
    .filter((item) => item.quantity > 0));

  const login = async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const loginId = String(form.get("loginId") || "").trim();
    const password = String(form.get("password") || "");
    try {
      const response = await fetch(`${API_BASE}/api/customer/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ login_id: loginId, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "로그인에 실패했습니다.");
      setSession(data);
      alert(`${data.user.user_name}님, 환영합니다.`);
      move("home");
    } catch (error) {
      alert(error.message === "Failed to fetch" ? "FastAPI 서버에 연결할 수 없습니다. 8001번 서버를 확인해주세요." : error.message);
    }
  };

  const signup = async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget).entries());
    if (data.password.length < 4) return alert("비밀번호는 4자 이상 입력해주세요.");
    if (data.password !== data.passwordConfirm) return alert("비밀번호가 서로 다릅니다.");
    try {
      const response = await fetch(`${API_BASE}/api/customer/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          login_id: data.loginId.trim(),
          password: data.password,
          user_name: data.name.trim(),
          email: data.email.trim(),
          phone: data.phone.trim(),
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "회원가입에 실패했습니다.");
      alert("MySQL 회원가입이 완료되었습니다. 로그인해주세요.");
      move("login");
    } catch (error) {
      alert(error.message === "Failed to fetch" ? "FastAPI 서버에 연결할 수 없습니다. 8001번 서버를 확인해주세요." : error.message);
    }
  };

  const findId = async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget).entries());
    try {
      const response = await fetch(`${API_BASE}/api/customer/find-id`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_name: data.name.trim(), email: data.email.trim() }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "아이디를 찾지 못했습니다.");
      alert(`회원님의 아이디는 ${result.login_id} 입니다.`);
      move("login");
    } catch (error) {
      alert(error.message === "Failed to fetch" ? "FastAPI 서버에 연결할 수 없습니다. 8001번 서버를 확인해주세요." : error.message);
    }
  };

  const resetPassword = async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget).entries());
    if (data.newPassword !== data.passwordConfirm) return alert("새 비밀번호가 서로 다릅니다.");
    try {
      const response = await fetch(`${API_BASE}/api/customer/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          login_id: data.loginId.trim(),
          email: data.email.trim(),
          new_password: data.newPassword,
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "비밀번호를 변경하지 못했습니다.");
      alert(result.message);
      move("login");
    } catch (error) {
      alert(error.message === "Failed to fetch" ? "FastAPI 서버에 연결할 수 없습니다. 8001번 서버를 확인해주세요." : error.message);
    }
  };

  const updateProfile = async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget).entries());
    try {
      const response = await fetch(`${API_BASE}/api/customer/profile`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          user_name: data.name.trim(),
          email: data.email.trim(),
          phone: data.phone.trim() || null,
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "회원정보를 수정하지 못했습니다.");
      setSession((current) => ({ ...current, user: result }));
      alert("회원정보가 수정되었습니다.");
      move("mypage");
    } catch (error) {
      alert(error.message === "Failed to fetch" ? "FastAPI 서버에 연결할 수 없습니다." : error.message);
    }
  };

  const logout = () => {
    setSession(null);
    alert("로그아웃되었습니다.");
    move("home");
  };

  const startCheckout = () => {
    if (!currentUser) {
      alert("주문하려면 먼저 로그인해주세요.");
      move("login");
      return;
    }
    move("checkout");
  };

  const submitOrder = async (event) => {
    event.preventDefault();
    if (!session?.access_token) return alert("로그인이 만료되었습니다. 다시 로그인해주세요.");
    const data = Object.fromEntries(new FormData(event.currentTarget).entries());
    try {
      const response = await fetch(`${API_BASE}/api/customer/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          receiver_name: data.receiverName.trim(),
          receiver_phone: data.receiverPhone.trim(),
          zipcode: data.zipcode.trim(),
          address1: data.address1.trim(),
          address2: data.address2.trim(),
          payment_method: data.paymentMethod,
          items: cart.map((item) => ({
            product_id: item.id,
            product_name: `${item.name} (${item.color}/${item.size})`,
            quantity: item.quantity,
            unit_price: item.price,
            variant_id: item.variant_id,
            sku: item.sku,
          })),
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "주문 저장에 실패했습니다.");
      setOrderResult({ ...result, payment_method: data.paymentMethod });
      setCart([]);
      move("order-complete");
    } catch (error) {
      alert(error.message === "Failed to fetch" ? "FastAPI 서버에 연결할 수 없습니다." : error.message);
    }
  };

  const confirmPayment = async () => {
    if (!orderResult?.order_id || !session?.access_token) return;
    if (!window.confirm(`${won(orderResult.total_amount)}을 결제하시겠습니까?`)) return;
    try {
      const response = await fetch(`${API_BASE}/api/customer/orders/${orderResult.order_id}/pay`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ payment_method: orderResult.payment_method || "CARD" }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "결제 승인에 실패했습니다.");
      setOrderResult((current) => ({ ...current, ...result }));
      alert(result.message);
    } catch (error) {
      alert(error.message === "Failed to fetch" ? "FastAPI 서버에 연결할 수 없습니다." : error.message);
    }
  };

  const openOrderHistory = async () => {
    if (!session?.access_token) {
      alert("로그인이 필요합니다.");
      move("login");
      return;
    }
    setOrdersLoading(true);
    move("orders");
    try {
      const response = await fetch(`${API_BASE}/api/customer/orders`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "주문내역을 불러오지 못했습니다.");
      setOrders(result);
    } catch (error) {
      alert(error.message === "Failed to fetch" ? "FastAPI 서버에 연결할 수 없습니다." : error.message);
      setOrders([]);
    } finally {
      setOrdersLoading(false);
    }
  };

  const openPaymentHistory = async () => {
    if (!session?.access_token) {
      alert("로그인이 필요합니다.");
      move("login");
      return;
    }
    move("payments");
    setPaymentsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/customer/orders/payments`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "결제내역을 불러오지 못했습니다.");
      setPayments(result);
    } catch (error) {
      alert(error.message);
      setPayments([]);
    } finally {
      setPaymentsLoading(false);
    }
  };

  const printReceipt = (payment) => {
    const popup = window.open("", "OFFIT_RECEIPT", "width=620,height=760");
    if (!popup) {
      alert("팝업 차단을 해제해주세요.");
      return;
    }
    popup.document.write(`<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>OFFIT 결제 영수증</title>
<style>body{font-family:Arial,sans-serif;padding:45px;color:#111}h1{letter-spacing:2px}dl{border-top:2px solid #111}div{display:flex;justify-content:space-between;padding:14px 4px;border-bottom:1px solid #ddd}dt{font-weight:bold}dd{margin:0}.total{font-size:20px;font-weight:bold}button{width:100%;margin-top:28px;padding:13px;color:#fff;background:#111;border:0}@media print{button{display:none}}</style>
</head>
<body>
<h1>OFFIT</h1>
<p>결제 영수증</p>
<dl>
<div>
<dt>주문번호</dt>
<dd>${payment.order_no}</dd>
</div>
<div>
<dt>결제수단</dt>
<dd>${paymentMethodName[payment.payment_method] || payment.payment_method || "-"}</dd>
</div>
<div>
<dt>결제상태</dt>
<dd>${paymentStatusName[payment.payment_status] || payment.payment_status}</dd>
</div>
<div>
<dt>결제일시</dt>
<dd>${payment.approved_at ? new Date(payment.approved_at).toLocaleString("ko-KR") : "-"}</dd>
</div>
<div class="total">
<dt>결제금액</dt>
<dd>${won(payment.approved_amount || payment.requested_amount)}</dd>
</div>
</dl>
<button onclick="window.print()">인쇄하기</button>
</body>
</html>`);
    popup.document.close();
  };

  const cancelOrder = async (orderId) => {
    if (!window.confirm("이 주문을 취소하시겠습니까?")) return;
    try {
      const response = await fetch(`${API_BASE}/api/customer/orders/${orderId}/cancel`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "주문을 취소하지 못했습니다.");
      setOrders((current) => current.map((order) => order.order_id === orderId ? { ...order, order_status: "CANCELLED" } : order));
      alert(result.message);
    } catch (error) {
      alert(error.message === "Failed to fetch" ? "FastAPI 서버에 연결할 수 없습니다." : error.message);
    }
  };

  const requestRefund = async (orderId) => {
    const reason = window.prompt("환불 사유를 입력해주세요.");
    if (reason === null) return;
    if (reason.trim().length < 2) return alert("환불 사유를 2자 이상 입력해주세요.");
    try {
      const response = await fetch(`${API_BASE}/api/customer/orders/${orderId}/refund`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ refund_reason: reason.trim() }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "환불을 신청하지 못했습니다.");
      setOrders((current) => current.map((order) => order.order_id === orderId ? { ...order, refund_status: "REQUESTED" } : order));
      alert(result.message);
    } catch (error) {
      alert(error.message === "Failed to fetch" ? "FastAPI 서버에 연결할 수 없습니다." : error.message);
    }
  };

  const addReview = async (event) => {
    event.preventDefault();
    const reviewForm = event.currentTarget;
    if (!currentUser) {
      alert("상품 후기는 로그인 후 작성할 수 있습니다.");
      setDetail(null);
      move("login");
      return;
    }
    const data = Object.fromEntries(new FormData(reviewForm).entries());
    const content = data.content.trim();
    if (content.length < 5) return alert("후기를 5자 이상 입력해주세요.");

    try {
      const response = await fetch(`${API_BASE}/api/customer/reviews`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          product_id: detail.id,
          rating: Number(data.rating),
          review_content: content,
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "후기를 등록하지 못했습니다.");

      setReviews((current) => [result, ...current]);
      reviewForm.reset();
      alert("상품 후기가 등록되었습니다.");
    } catch (error) {
      alert(error.message === "Failed to fetch"
        ? "FastAPI 서버에 연결할 수 없습니다. 8001번 서버를 확인해주세요."
        : error.message);
    }
  };

  const deleteReview = async (reviewId) => {
    if (!window.confirm("이 후기를 삭제하시겠습니까?")) return;
    try {
      const response = await fetch(`${API_BASE}/api/customer/reviews/${reviewId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "후기를 삭제하지 못했습니다.");
      setReviews((current) => current.filter((review) => review.id !== reviewId));
      alert(result.message);
    } catch (error) {
      alert(error.message === "Failed to fetch"
        ? "FastAPI 서버에 연결할 수 없습니다. 8001번 서버를 확인해주세요."
        : error.message);
    }
  };

  const addQuestion = (event) => {
    event.preventDefault();
    if (!currentUser) {
      alert("상품 문의는 로그인 후 등록할 수 있습니다.");
      setDetail(null);
      move("login");
      return;
    }
    const data = Object.fromEntries(new FormData(event.currentTarget).entries());
    const content = data.content.trim();
    if (content.length < 5) return alert("문의 내용을 5자 이상 입력해주세요.");
    setQuestions((current) => [{
      id: Date.now(), productId: qnaProduct.id, userId: currentUser.user_id,
      userName: currentUser.user_name, category: data.category, content,
      status: "WAITING", createdAt: new Date().toISOString(),
    }, ...current]);
    event.currentTarget.reset();
    alert("상품 문의가 등록되었습니다.");
  };

  const deleteQuestion = (questionId) => {
    if (!window.confirm("이 문의를 삭제하시겠습니까?")) return;
    setQuestions((current) => current.filter((question) => question.id !== questionId));
  };

  const openQuestionPage = (product) => {
    setQnaProduct(product);
    setDetail(null);
    setPage("qna");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const addAddress = async (event) => {
    event.preventDefault();
    if (!session?.access_token) {
      alert("로그인이 필요합니다.");
      move("login");
      return;
    }
    const data = Object.fromEntries(new FormData(event.currentTarget).entries());
    try {
      const response = await fetch(`${API_BASE}/api/customer/addresses`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          address_name: data.addressName.trim(),
          receiver_name: data.receiver.trim(),
          receiver_phone: data.phone.trim(),
          zipcode: data.zipcode.trim(),
          address1: data.address1.trim(),
          address2: data.address2.trim() || null,
          default_yn: addresses.length === 0 || data.isDefault === "on" ? "Y" : "N",
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "배송지를 등록하지 못했습니다.");

      const address = {
        id: result.address_id,
        name: result.address_name,
        receiver: result.receiver_name,
        phone: result.receiver_phone,
        zipcode: result.zipcode,
        address1: result.address1,
        address2: result.address2 || "",
        isDefault: result.default_yn === "Y",
      };
      setAddresses((current) => [
        address,
        ...current.map((item) => address.isDefault ? { ...item, isDefault: false } : item),
      ]);
      event.currentTarget.reset();
      alert("배송지가 등록되었습니다.");
    } catch (error) {
      alert(error.message === "Failed to fetch"
        ? "FastAPI 서버에 연결할 수 없습니다. 8001번 서버를 확인해주세요."
        : error.message);
    }
  };

  const setDefaultAddress = async (addressId) => {
    try {
      const response = await fetch(`${API_BASE}/api/customer/addresses/${addressId}/default`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "기본 배송지를 변경하지 못했습니다.");
      setAddresses((current) => current.map((item) => ({
        ...item,
        isDefault: item.id === addressId,
      })));
      alert(result.message);
    } catch (error) {
      alert(error.message === "Failed to fetch"
        ? "FastAPI 서버에 연결할 수 없습니다. 8001번 서버를 확인해주세요."
        : error.message);
    }
  };

  const deleteAddress = async (addressId) => {
    if (!window.confirm("이 배송지를 삭제하시겠습니까?")) return;
    try {
      const deletedAddress = addresses.find((item) => item.id === addressId);
      const response = await fetch(`${API_BASE}/api/customer/addresses/${addressId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "배송지를 삭제하지 못했습니다.");
      setAddresses((current) => {
        const next = current.filter((item) => item.id !== addressId);
        if (deletedAddress?.isDefault && next.length > 0) {
          next[0] = { ...next[0], isDefault: true };
        }
        return next;
      });
      alert(result.message);
    } catch (error) {
      alert(error.message === "Failed to fetch"
        ? "FastAPI 서버에 연결할 수 없습니다. 8001번 서버를 확인해주세요."
        : error.message);
    }
  };

  return (
    <div className="app">
      <div className="announcement">OFFIT 신규 회원 첫 구매 10% 할인 · 50,000원 이상 무료배송</div>

      <header className="header">
        <div className="header-row">
          <button className="logo" onClick={() => move("home")}>OFFIT<span>EVERYDAY DIFFERENT</span>
</button>
          <form className="search" onSubmit={search}>
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="찾고 싶은 상품을 검색하세요" />
            <button>SEARCH</button>
          </form>
          <div className="utilities">
            {currentUser ? <>
<button onClick={() => move("mypage")}>{currentUser.user_name}님</button>
<button onClick={logout}>LOGOUT</button>
</> : <button onClick={() => move("login")}>LOGIN</button>}
            <button onClick={() => move("wish")}>WISH <b>{likes.length}</b>
</button>
            <button onClick={() => move("cart")}>CART <b>{cartCount}</b>
</button>
          </div>
        </div>
        <nav>
          <button onClick={() => move("home")}>HOME</button>
          <button onClick={() => showCategory("전체")}>NEW</button>
          <button onClick={() => move("best")}>BEST</button>
          <button onClick={() => showCategory("상의")}>TOP</button>
          <button onClick={() => showCategory("아우터")}>OUTER</button>
          <button onClick={() => showCategory("하의")}>BOTTOM</button>
          <button onClick={() => showCategory("신발")}>SHOES</button>
          <button onClick={() => move("qna")}>Q&amp;A</button>
          <button onClick={() => move("notice")}>NOTICE</button>
        </nav>
      </header>

      <main>
        {page === "home" && <>
          <section className="hero">
            <img src="/images/offit-collection.png" alt="OFFIT 스타일 컬렉션" />
            <div className="hero-copy">
              <p>OFFIT 2026 COLLECTION</p>
              <h1>EVERYDAY,<br />DIFFERENT</h1>
              <span>BASIC · CASUAL · DAILY · MODERN</span>
              <button onClick={() => showCategory("전체")}>SHOP NOW</button>
            </div>
          </section>

          <section className="category-strip">
            <button onClick={() => showCategory("상의")}>
<span>01</span>
<strong>TOP</strong>
<small>셔츠·니트·후드티</small>
</button>
            <button onClick={() => showCategory("아우터")}>
<span>02</span>
<strong>OUTER</strong>
<small>재킷·가디건</small>
</button>
            <button onClick={() => showCategory("하의")}>
<span>03</span>
<strong>BOTTOM</strong>
<small>스커트·팬츠</small>
</button>
            <button onClick={() => showCategory("신발")}>
<span>04</span>
<strong>SHOES</strong>
<small>로퍼·스니커즈</small>
</button>
          </section>

          <ProductSection title="NEW ARRIVALS" description="오프핏의 새로운 상품을 만나보세요" items={products} likes={likes} onLike={toggleLike} onCart={addCart} onDetail={openDetail} />

          <section className="brand-banner">
            <img src="/images/offit-lookbook.png" alt="OFFIT 룩북" />
            <div>
<p>OFFIT LOOKBOOK</p>
<h2>취향에 맞는 오늘의 스타일</h2>
<button onClick={() => move("best")}>VIEW LOOKBOOK</button>
</div>
          </section>
        </>}

        {(page === "shop" || page === "best") && <section className="content-page">
          <div className="page-title">
<p>OFFIT COLLECTION</p>
<h1>{page === "best" ? "BEST" : category === "전체" ? "NEW ARRIVALS" : category}</h1>
</div>
          <div className="shop-layout">
            <aside>
<h3>CATEGORY</h3>{categories.map((item) => <button className={category === item ? "selected" : ""} onClick={() => setCategory(item)} key={item}>{item}</button>)}</aside>
            <div className="results">
<div className="result-line">
<span>총 {page === "best" ? products.filter((p) => p.best).length : visibleProducts.length}개</span>{keyword && <button onClick={() => { setKeyword(""); setQuery(""); setCategory("전체"); }}>검색 초기화</button>}</div>
              <ProductGrid items={page === "best" ? products.filter((p) => p.best) : visibleProducts} likes={likes} onLike={toggleLike} onCart={addCart} onDetail={openDetail} />
            </div>
          </div>
        </section>}

        {page === "wish" && <section className="content-page">
<div className="page-title">
<p>MY PAGE</p>
<h1>WISH LIST</h1>
</div>{likes.length ? <ProductGrid items={products.filter((p) => likes.includes(p.id))} likes={likes} onLike={toggleLike} onCart={addCart} onDetail={openDetail} /> : <Empty text="찜한 상품이 없습니다." action={() => showCategory("전체")} />}</section>}

        {page === "recent" && <section className="content-page">
<div className="page-title">
<p>MY PAGE</p>
<h1>RECENTLY VIEWED</h1>
</div>{recentViewed.length ? <>
<div className="recent-toolbar">
<span>최근 본 상품 {recentViewed.length}개</span>
<button onClick={() => setRecentViewed([])}>전체 삭제</button>
</div>
<ProductGrid items={recentViewed.map((id) => products.find((product) => product.id === id)).filter(Boolean)} likes={likes} onLike={toggleLike} onCart={addCart} onDetail={openDetail} />
</> : <Empty text="최근 본 상품이 없습니다." action={() => showCategory("전체")} />}</section>}

        {page === "cart" && <section className="content-page">
<div className="page-title">
<p>ORDER</p>
<h1>SHOPPING CART</h1>
</div>{cart.length === 0 ? <Empty text="장바구니가 비어 있습니다." action={() => showCategory("전체")} /> : <div className="cart-layout">
<div className="cart-list">{cart.map((item) => <article key={item.cartKey}>
<img src={item.image} alt={item.name} />
<div>
<small>{item.category}</small>
<h3>{item.name}</h3>
<p className="cart-option">색상 {item.color} · 사이즈 {item.size}</p>
<strong>{won(item.price)}</strong>
</div>
<div className="quantity">
<button onClick={() => changeQuantity(item.cartKey, -1)}>−</button>
<span>{item.quantity}</span>
<button onClick={() => changeQuantity(item.cartKey, 1)}>+</button>
</div>
<b>{won(item.price * item.quantity)}</b>
</article>)}</div>
<aside className="summary">
<h2>ORDER SUMMARY</h2>
<p>
<span>상품 금액</span>
<b>{won(cartTotal)}</b>
</p>
<p>
<span>배송비</span>
<b>{cartTotal >= 50000 ? "무료" : "3,000원"}</b>
</p>
<hr />
<p className="total">
<span>총 결제 금액</span>
<b>{won(cartTotal + (cartTotal >= 50000 ? 0 : 3000))}</b>
</p>
<button onClick={startCheckout}>주문하기</button>
</aside>
</div>}</section>}

        {page === "checkout" && <section className="content-page">
<div className="page-title">
<p>ORDER</p>
<h1>CHECKOUT</h1>
</div>{cart.length === 0 ? <Empty text="주문할 상품이 없습니다." action={() => showCategory("전체")} /> : <form className="checkout-layout" onSubmit={submitOrder}>
<div className="delivery-form">
<h2>배송 정보</h2>
<label>받는 분<input name="receiverName" required defaultValue={currentUser?.user_name || ""} />
</label>
<label>휴대폰 번호<input name="receiverPhone" required defaultValue={currentUser?.phone || ""} placeholder="010-0000-0000" />
</label>
<div className="address-row">
<label>우편번호<input name="zipcode" required placeholder="12345" />
</label>
<label>기본 주소<input name="address1" required placeholder="도로명 주소" />
</label>
</div>
<label>상세 주소<input name="address2" placeholder="동·호수 등 상세 주소" />
</label>
<h2>결제 방법</h2>
<div className="payment-options">
<label>
<input type="radio" name="paymentMethod" value="CARD" defaultChecked /> 신용·체크카드</label>
<label>
<input type="radio" name="paymentMethod" value="KAKAOPAY" /> 카카오페이</label>
<label>
<input type="radio" name="paymentMethod" value="TOSS" /> 토스페이</label>
</div>
<p className="demo-payment">프로젝트 시제품으로 실제 결제는 진행되지 않으며 결제대기 상태로 저장됩니다.</p>
</div>
<aside className="summary">
<h2>ORDER SUMMARY</h2>{cart.map((item) => <p key={item.cartKey}>
<span>{item.name} ({item.color}/{item.size}) × {item.quantity}</span>
<b>{won(item.price * item.quantity)}</b>
</p>)}<hr />
<p>
<span>배송비</span>
<b>{cartTotal >= 50000 ? "무료" : "3,000원"}</b>
</p>
<p className="total">
<span>최종 금액</span>
<b>{won(cartTotal + (cartTotal >= 50000 ? 0 : 3000))}</b>
</p>
<button>주문 확정</button>
</aside>
</form>}</section>}

        {page === "order-complete" && <section className="order-complete">
<span>OFFIT PAYMENT</span>
<h1>{orderResult?.payment_status === "DONE" ? "결제가 완료되었습니다." : "주문이 접수되었습니다."}</h1>
<p>주문번호</p>
<strong>{orderResult?.order_no}</strong>
<dl>
<div>
<dt>상품 금액</dt>
<dd>{won(orderResult?.product_amount || 0)}</dd>
</div>
<div>
<dt>배송비</dt>
<dd>{won(orderResult?.shipping_amount || 0)}</dd>
</div>
<div>
<dt>총 결제 금액</dt>
<dd>{won(orderResult?.total_amount || 0)}</dd>
</div>
<div>
<dt>결제 방법</dt>
<dd>{orderResult?.payment_method === "KAKAOPAY" ? "카카오페이" : orderResult?.payment_method === "TOSS" ? "토스페이" : "신용·체크카드"}</dd>
</div>
<div>
<dt>결제 상태</dt>
<dd>{orderResult?.payment_status === "DONE" ? "결제완료" : "결제대기"}</dd>
</div>
</dl>{orderResult?.payment_status === "DONE" ? <button onClick={() => move("home")}>쇼핑 계속하기</button> : <button className="payment-button" onClick={confirmPayment}>결제하기</button>}</section>}

        {page === "orders" && <section className="content-page">
<div className="page-title">
<p>MY OFFIT</p>
<h1>ORDER HISTORY</h1>
</div>{ordersLoading ? <div className="empty">
<h2>주문내역을 불러오는 중입니다.</h2>
</div> : orders.length === 0 ? <Empty text="주문내역이 없습니다." action={() => showCategory("전체")} /> : <div className="order-history">{orders.map((order) => <article key={order.order_id}>
<div className="order-head">
<div>
<time>{new Date(order.ordered_at).toLocaleString("ko-KR")}</time>
<strong>{order.order_no}</strong>
</div>
<span className={`status status-${order.order_status.toLowerCase()}`}>{orderStatusName[order.order_status] || order.order_status}</span>
</div>
<div className="order-body">
<div>
<p>{order.first_product_name}{order.item_count > 1 ? ` 외 ${order.item_count - 1}건` : ""}</p>
<small>상품 {order.item_count}개 · 배송비 {won(order.shipping_amount)}</small>{order.refund_status && <span className="refund-state">환불 상태: {order.refund_status === "REQUESTED" ? "신청완료" : order.refund_status}</span>}</div>
<div className="order-price-actions">
<strong>{won(order.total_amount)}</strong>{["ORDERED", "PAYMENT_PENDING", "PAID"].includes(order.order_status) && <button onClick={() => cancelOrder(order.order_id)}>주문 취소</button>}{["DELIVERED", "COMPLETED"].includes(order.order_status) && !order.refund_status && <button onClick={() => requestRefund(order.order_id)}>환불 신청</button>}</div>
</div>
<div className="delivery-steps">
<span className={["PAYMENT_PENDING"].includes(order.order_status) ? "active" : ""}>결제대기</span>
<span className={["PAID", "PREPARING"].includes(order.order_status) ? "active" : ""}>배송준비</span>
<span className={order.order_status === "SHIPPING" ? "active" : ""}>배송중</span>
<span className={["DELIVERED", "COMPLETED"].includes(order.order_status) ? "active" : ""}>배송완료</span>
</div>
</article>)}</div>}</section>}

        {page === "payments" && <section className="content-page">
<div className="page-title">
<p>MY OFFIT</p>
<h1>PAYMENT HISTORY</h1>
</div>{paymentsLoading ? <div className="empty">
<h2>결제내역을 불러오는 중입니다.</h2>
</div> : payments.length === 0 ? <Empty text="결제내역이 없습니다." action={() => showCategory("전체")} /> : <div className="payment-history">{payments.map((payment) => <article key={payment.payment_id}>
<div className="payment-head">
<div>
<time>{new Date(payment.approved_at || payment.requested_at).toLocaleString("ko-KR")}</time>
<strong>{payment.order_no}</strong>
</div>
<span className={`payment-status payment-${payment.payment_status.toLowerCase()}`}>{paymentStatusName[payment.payment_status] || payment.payment_status}</span>
</div>
<dl>
<div>
<dt>결제수단</dt>
<dd>{paymentMethodName[payment.payment_method] || payment.payment_method || "-"}</dd>
</div>
<div>
<dt>결제대행사</dt>
<dd>{payment.pg_provider}</dd>
</div>
<div>
<dt>요청금액</dt>
<dd>{won(payment.requested_amount)}</dd>
</div>
<div>
<dt>승인금액</dt>
<dd>{won(payment.approved_amount)}</dd>
</div>{Number(payment.cancelled_amount) > 0 && <div>
<dt>취소금액</dt>
<dd>{won(payment.cancelled_amount)}</dd>
</div>}</dl>
<div className="payment-actions">{payment.receipt_url && <button onClick={() => window.open(payment.receipt_url, "_blank", "noopener,noreferrer")}>PG 영수증</button>}<button disabled={payment.payment_status !== "DONE"} onClick={() => printReceipt(payment)}>영수증 보기</button>
</div>
</article>)}</div>}</section>}

        {page === "login" && <section className="login-page">
<form onSubmit={login}>
<h1>OFFIT</h1>
<p>회원 로그인을 해주세요.</p>
<input name="loginId" required placeholder="아이디" autoComplete="username" />
<input name="password" required type="password" placeholder="비밀번호" autoComplete="current-password" />
<button>LOGIN</button>
<div>
<button type="button" onClick={() => move("find-id")}>아이디 찾기</button>
<button type="button" onClick={() => move("reset-password")}>비밀번호 찾기</button>
<button type="button" onClick={() => move("signup")}>회원가입</button>
</div>
</form>
</section>}

        {page === "find-id" && <section className="login-page signup-page">
<form onSubmit={findId}>
<h1>FIND ID</h1>
<p>가입할 때 입력한 이름과 이메일을 입력해주세요.</p>
<label>이름<input name="name" required placeholder="이름" />
</label>
<label>이메일<input name="email" required type="email" placeholder="offit@example.com" />
</label>
<button>아이디 찾기</button>
<div>
<button type="button" onClick={() => move("login")}>로그인으로 돌아가기</button>
</div>
</form>
</section>}

        {page === "reset-password" && <section className="login-page signup-page">
<form onSubmit={resetPassword}>
<h1>RESET PASSWORD</h1>
<p>회원정보를 확인한 뒤 새 비밀번호로 변경합니다.</p>
<label>아이디<input name="loginId" required placeholder="아이디" autoComplete="username" />
</label>
<label>이메일<input name="email" required type="email" placeholder="offit@example.com" />
</label>
<label>새 비밀번호<input name="newPassword" required minLength="4" type="password" placeholder="4자 이상 입력" autoComplete="new-password" />
</label>
<label>새 비밀번호 확인<input name="passwordConfirm" required minLength="4" type="password" placeholder="새 비밀번호를 다시 입력" autoComplete="new-password" />
</label>
<button>비밀번호 변경</button>
<div>
<button type="button" onClick={() => move("login")}>로그인으로 돌아가기</button>
</div>
</form>
</section>}

        {page === "signup" && <section className="login-page signup-page">
<form onSubmit={signup}>
<h1>JOIN OFFIT</h1>
<p>오프핏 회원이 되어 다양한 혜택을 만나보세요.</p>
<label>아이디<input name="loginId" required minLength="4" placeholder="4자 이상 입력" autoComplete="username" />
</label>
<label>비밀번호<input name="password" required minLength="4" type="password" placeholder="4자 이상 입력" autoComplete="new-password" />
</label>
<label>비밀번호 확인<input name="passwordConfirm" required minLength="4" type="password" placeholder="비밀번호를 다시 입력" autoComplete="new-password" />
</label>
<label>이름<input name="name" required placeholder="이름" />
</label>
<label>이메일<input name="email" required type="email" placeholder="offit@example.com" />
</label>
<label>휴대폰 번호<input name="phone" required placeholder="010-0000-0000" />
</label>
<label className="terms">
<input name="terms" required type="checkbox" /> 이용약관 및 개인정보 수집에 동의합니다.</label>
<button>회원가입</button>
<div>
<span>이미 회원이신가요?</span>
<button type="button" onClick={() => move("login")}>로그인</button>
</div>
</form>
</section>}

        {page === "mypage" && <section className="content-page">
<div className="page-title">
<p>MY OFFIT</p>
<h1>MY PAGE</h1>
</div>{currentUser ? <div className="member-card">
<p>WELCOME TO OFFIT</p>
<h2>{currentUser.user_name}님, 반갑습니다.</h2>
<dl>
<div>
<dt>회원번호</dt>
<dd>{currentUser.user_id}</dd>
</div>
<div>
<dt>아이디</dt>
<dd>{currentUser.login_id}</dd>
</div>
<div>
<dt>이메일</dt>
<dd>{currentUser.email}</dd>
</div>
<div>
<dt>휴대폰</dt>
<dd>{currentUser.phone || "미등록"}</dd>
</div>
<div>
<dt>권한</dt>
<dd>{currentUser.role_code}</dd>
</div>
</dl>
<div className="member-actions">
<button onClick={openOrderHistory}>주문내역</button>
<button onClick={openPaymentHistory}>결제내역</button>
<button onClick={() => move("profile-edit")}>회원정보 수정</button>
<button onClick={() => move("addresses")}>배송지 관리 {addresses.length}</button>
<button onClick={() => move("recent")}>최근 본 상품 {recentViewed.length}</button>
<button onClick={() => move("wish")}>찜 목록 {likes.length}</button>
<button onClick={() => move("cart")}>장바구니 {cartCount}</button>
<button onClick={logout}>로그아웃</button>
</div>
</div> : <Empty text="로그인이 필요합니다." action={() => move("login")} />}</section>}

        {page === "profile-edit" && <section className="login-page signup-page">
<form onSubmit={updateProfile}>
<h1>EDIT PROFILE</h1>
<p>MySQL에 저장된 회원정보를 수정합니다.</p>
<label>아이디<input value={currentUser?.login_id || ""} disabled />
</label>
<label>이름<input name="name" required defaultValue={currentUser?.user_name || ""} />
</label>
<label>이메일<input name="email" required type="email" defaultValue={currentUser?.email || ""} />
</label>
<label>휴대폰 번호<input name="phone" defaultValue={currentUser?.phone || ""} placeholder="010-0000-0000" />
</label>
<button>수정 완료</button>
<div>
<button type="button" onClick={() => move("mypage")}>마이페이지로 돌아가기</button>
</div>
</form>
</section>}

        {page === "addresses" && <section className="content-page">
<div className="page-title">
<p>MY OFFIT</p>
<h1>ADDRESS BOOK</h1>
</div>
<div className="address-book">
<form className="address-form" onSubmit={addAddress}>
<h2>새 배송지 등록</h2>
<label>배송지 이름<input name="addressName" required placeholder="집, 회사 등" />
</label>
<div>
<label>받는 분<input name="receiver" required defaultValue={currentUser?.user_name || ""} />
</label>
<label>휴대폰 번호<input name="phone" required defaultValue={currentUser?.phone || ""} placeholder="010-0000-0000" />
</label>
</div>
<div>
<label>우편번호<input name="zipcode" required placeholder="12345" />
</label>
<label>기본 주소<input name="address1" required placeholder="도로명 주소" />
</label>
</div>
<label>상세 주소<input name="address2" placeholder="동·호수 등 상세 주소" />
</label>
<label className="default-check">
<input name="isDefault" type="checkbox" /> 기본 배송지로 설정</label>
<button>배송지 등록</button>
</form>
<div className="address-list">
<h2>등록된 배송지</h2>{addressesLoading ? <p className="no-review">배송지를 불러오는 중입니다.</p> : addresses.length === 0 ? <p className="no-review">등록된 배송지가 없습니다.</p> : addresses.map((address) => <article key={address.id}>
<div>
<h3>{address.name}{address.isDefault && <b>기본 배송지</b>}</h3>
<p>{address.receiver} · {address.phone}</p>
<p>[{address.zipcode}] {address.address1} {address.address2}</p>
</div>
<div>
<button disabled={address.isDefault} onClick={() => setDefaultAddress(address.id)}>기본 설정</button>
<button onClick={() => deleteAddress(address.id)}>삭제</button>
</div>
</article>)}</div>
</div>
</section>}

        {page === "qna" && qnaProduct && <section className="content-page">
<div className="page-title">
<p>PRODUCT</p>
<h1>Q&amp;A</h1>
</div>
<div className="qna-page">
<label className="qna-product-selector">
<span>문의할 상품 선택</span>
<select
value={String(qnaProduct.id)}
onChange={(event) => {
const selectedProduct = products.find((product) => String(product.id) === event.target.value);
if (selectedProduct) setQnaProduct(selectedProduct);
}}
>
{products.map((product) => <option key={product.id} value={String(product.id)}>{product.name}</option>)}
</select>
</label>
<div className="qna-product">
<img src={qnaProduct.image} alt={qnaProduct.name} />
<div>
<small>{qnaProduct.category}</small>
<h2>{qnaProduct.name}</h2>
<strong>{won(qnaProduct.price)}</strong>
<button onClick={() => openDetail(qnaProduct)}>상품 다시 보기</button>
</div>
</div>{currentUser ? <form className="qna-form" onSubmit={addQuestion}>
<select name="category" defaultValue="상품">
<option>상품</option>
<option>사이즈</option>
<option>배송</option>
<option>교환·반품</option>
</select>
<textarea name="content" required minLength="5" placeholder="상품 문의를 5자 이상 작성해주세요." />
<button>문의 등록</button>
</form> : <button className="review-login" onClick={() => move("login")}>로그인 후 상품 문의</button>}<div className="qna-list">{questions.filter((question) => question.productId === qnaProduct.id).length === 0 ? <p className="no-review">등록된 상품 문의가 없습니다.</p> : questions.filter((question) => question.productId === qnaProduct.id).map((question) => <article key={question.id}>
<div className="qna-head">
<b>{question.category}</b>
<strong>{question.status === "ANSWERED" ? "답변완료" : "답변대기"}</strong>
<span>{question.userName} · {new Date(question.createdAt).toLocaleDateString("ko-KR")}</span>
</div>
<p>{question.content}</p>{question.userId === currentUser?.user_id && <button onClick={() => deleteQuestion(question.id)}>삭제</button>}</article>)}</div>
</div>
</section>}

        {page === "notice" && <section className="content-page">
<div className="page-title">
<p>COMMUNITY</p>
<h1>NOTICE</h1>
</div>
<div className="notices">{notices.map((notice) => <article key={notice.id} className={selectedNotice?.id === notice.id ? "notice-open" : ""}>
<button className="notice-row" onClick={() => setSelectedNotice(selectedNotice?.id === notice.id ? null : notice)}>
<b>{notice.type}</b>
<span>{notice.title}</span>
<time>{notice.date}</time>
</button>{selectedNotice?.id === notice.id && <div className="notice-detail">
<h2>{notice.title}</h2>
<p>{notice.content}</p>
<button onClick={() => setSelectedNotice(null)}>닫기</button>
</div>}</article>)}</div>
</section>}
      </main>

      {detail && <div className="modal-bg" onMouseDown={() => setDetail(null)}>
<article className="modal review-modal" onMouseDown={(e) => e.stopPropagation()}>
<button className="close" onClick={() => setDetail(null)}>×</button>
<img src={detail.image} alt={detail.name} />
<div className="modal-info">
<small>{detail.category}</small>
<h2>{detail.name}</h2>
<p>{detail.description}</p>
<del>{won(detail.originalPrice)}</del>
<strong>{won(detail.price)}</strong>
<label>색상<select value={selectedColor} onChange={(event) => setSelectedColor(event.target.value)}>
<option value="" disabled>색상을 선택하세요</option>
{(detail.colors?.length ? detail.colors : ["베이지", "차콜", "블랙"]).map((color) => <option key={color}>{color}</option>)}
</select>
</label>
<label>사이즈<select value={selectedSize} onChange={(event) => setSelectedSize(event.target.value)}>
<option value="" disabled>사이즈를 선택하세요</option>
{(detail.sizes?.length ? detail.sizes : ["S", "M", "L"]).map((size) => <option key={size}>{size}</option>)}
</select>
</label>
<p className="stock">남은 재고 {detail.stock}개</p>
<div className="modal-actions">
<button onClick={() => shareProduct(detail)}>SHARE</button>
<button onClick={() => toggleLike(detail.id)}>{likes.includes(detail.id) ? "♥ WISH" : "♡ WISH"}</button>
<button onClick={() => addCart(detail, selectedColor, selectedSize)}>ADD TO CART</button>
</div>
<section className="review-section">
<div className="review-title">
<h3>REVIEW</h3>
<span>{reviews.filter((review) => review.productId === detail.id).length}개</span>
</div>{reviewsLoading ? <p className="no-review">후기를 불러오는 중입니다.</p> : currentUser ? <form className="review-form" onSubmit={addReview}>
<select name="rating" defaultValue="5" aria-label="별점">
<option value="5">★★★★★ 5점</option>
<option value="4">★★★★☆ 4점</option>
<option value="3">★★★☆☆ 3점</option>
<option value="2">★★☆☆☆ 2점</option>
<option value="1">★☆☆☆☆ 1점</option>
</select>
<textarea name="content" required minLength="5" placeholder="상품 후기를 5자 이상 작성해주세요." />
<button>후기 등록</button>
</form> : <button className="review-login" onClick={() => { setDetail(null); move("login"); }}>로그인 후 후기 작성</button>}<div className="review-list">{reviews.filter((review) => review.productId === detail.id).length === 0 ? <p className="no-review">첫 번째 후기를 작성해주세요.</p> : reviews.filter((review) => review.productId === detail.id).map((review) => <article key={review.id}>
<div>
<strong>{"★".repeat(review.rating)}<i>{"★".repeat(5 - review.rating)}</i>
</strong>
<span>{review.userName} · {new Date(review.createdAt).toLocaleDateString("ko-KR")}</span>
</div>
<p>{review.content}</p>{review.userId === currentUser?.user_id && <button onClick={() => deleteReview(review.id)}>삭제</button>}</article>)}</div>
</section>
</div>
</article>
</div>}

      <footer>
<div>
<h2>OFFIT</h2>
<p>EVERYDAY DIFFERENT</p>
</div>
<div>
<b>CUSTOMER CENTER</b>
<p>평일 10:00 - 17:00</p>
</div>
<div>
<b>SHOP GUIDE</b>
<p>이용약관 · 개인정보처리방침 · 배송안내</p>
</div>
<small>© 2026 OFFIT. React FastAPI MySQL Project.</small>
</footer>
    </div>
  );
}

function ProductSection({ title, description, items, ...props }) {
  return <section className="product-section">
<div className="section-head">
<p>OFFIT SELECT</p>
<h2>{title}</h2>
<span>{description}</span>
</div>
<ProductGrid items={items} {...props} />
</section>;
}

function ProductGrid({ items, likes, onLike, onDetail }) {
  return <div className="product-grid">{items.map((product) => {
    const sale = Math.round((product.originalPrice - product.price) / product.originalPrice * 100);
    return <article className="product" key={product.id}>
<div className={`photo product-photo-${product.id}`}>
<img src={product.image} alt={product.name} />
<button className={likes.includes(product.id) ? "liked" : ""} onClick={() => onLike(product.id)}>{likes.includes(product.id) ? "♥" : "♡"}</button>{product.best && <b>BEST</b>}</div>
<div className="product-info">
<small>{product.category}</small>
<button className="name" onClick={() => onDetail(product)}>{product.name}</button>
<del>{won(product.originalPrice)}</del>
<p>
<em>{sale}%</em>
<strong>{won(product.price)}</strong>
</p>
<span>무료배송</span>
<button className="add" onClick={() => onDetail(product)}>옵션 선택</button>
</div>
</article>;
  })}</div>;
}

function Empty({ text, action }) {
  return <div className="empty">
<span>OFFIT</span>
<h2>{text}</h2>
<button onClick={action}>쇼핑 계속하기</button>
</div>;
}
