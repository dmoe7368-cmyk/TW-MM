// Firebase Configuration
const firebaseConfig = {
  apiKey: "AIzaSyDE11cAUZfJoZMMCF-eyqGDUioYDQSCWrs",
  authDomain: "tw-fpl-tour.firebaseapp.com",
  projectId: "tw-fpl-tour",
  storageBucket: "tw-fpl-tour.firebasestorage.app",
  messagingSenderId: "1023019839565",
  appId: "1:1023019839565:web:e91650d5c475c54a63ec04",
  measurementId: "G-48KP6S02RK"
};

// Firebase Initialize
firebase.initializeApp(firebaseConfig);

const db = firebase.firestore();
const auth = firebase.auth();

// 🛑 Error တက်တတ်သဖြင့် Analytics ကို ခေတ္တပိတ်ထားပါသည်
// const analytics = firebase.analytics();

console.log("TW MM Tournament - Firebase Connected! 🏆");
