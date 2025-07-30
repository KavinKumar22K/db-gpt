import { ChatContext, ChatContextProvider } from '@/app/chat-context';
import SideBar from '@/components/layout/side-bar';
import FloatHelper from '@/new-components/layout/FloatHelper';
import { STORAGE_LANG_KEY, STORAGE_USERINFO_KEY, STORAGE_USERINFO_VALID_TIME_KEY } from '@/utils/constants/index';
import { App, ConfigProvider, MappingAlgorithm, theme } from 'antd';
import enUS from 'antd/locale/en_US';
import zhCN from 'antd/locale/zh_CN';
import classNames from 'classnames';
import type { AppProps } from 'next/app';
import Head from 'next/head';
import { useRouter } from 'next/router';
import React, { useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import '../app/i18n';
import '../nprogress.css';
import '../styles/globals.css';
// import TopProgressBar from '@/components/layout/top-progress-bar';

const antdDarkTheme: MappingAlgorithm = (seedToken, mapToken) => {
  return {
    ...theme.darkAlgorithm(seedToken, mapToken),
    colorBgBase: '#232734',
    colorBorder: '#828282',
    colorBgContainer: '#232734',
  };
};

function CssWrapper({ children }: { children: React.ReactElement }) {
  const { mode } = useContext(ChatContext);
  const { i18n } = useTranslation();

  useEffect(() => {
    if (mode) {
      document.body?.classList?.add(mode);
      if (mode === 'light') {
        document.body?.classList?.remove('dark');
      } else {
        document.body?.classList?.remove('light');
      }
    }
  }, [mode]);

  useEffect(() => {
    i18n.changeLanguage?.(window.localStorage.getItem(STORAGE_LANG_KEY) || 'zh');
  }, [i18n]);

  return (
    <div>
      {/* <TopProgressBar /> */}
      {children}
    </div>
  );
}

function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const { isMenuExpand, mode } = useContext(ChatContext);
  const { i18n } = useTranslation();
  const [isLogin, setIsLogin] = useState(false);

  const router = useRouter();

  // 登录检测
  const handleAuth = async () => {
    setIsLogin(false);
    
    // Check if we're on the login page
    if (router.pathname === '/login') {
      setIsLogin(true);
      return;
    }

    // Check for existing session
    const userInfo = localStorage.getItem(STORAGE_USERINFO_KEY);
    const validTime = localStorage.getItem(STORAGE_USERINFO_VALID_TIME_KEY);
    
    if (userInfo && validTime) {
      const now = Date.now();
      const stored = parseInt(validTime);
      // Check if session is still valid (30 days)
      if (now - stored < 30 * 24 * 60 * 60 * 1000) {
        setIsLogin(true);
        return;
      }
    }

    // Try to authenticate with session cookie
    try {
      const response = await fetch('/api/v1/auth/me', {
        credentials: 'include',
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data?.user) {
          const user = result.data.user;
          localStorage.setItem(STORAGE_USERINFO_KEY, JSON.stringify(user));
          localStorage.setItem(STORAGE_USERINFO_VALID_TIME_KEY, Date.now().toString());
          setIsLogin(true);
          return;
        }
      }
    } catch (error) {
      console.log('Auth check failed:', error);
    }

    // Redirect to login if not authenticated
    router.push(`/login?redirect=${encodeURIComponent(router.asPath)}`);
  };

  useEffect(() => {
    handleAuth();
  }, []);

  if (!isLogin) {
    return null;
  }

  const renderContent = () => {
    if (router.pathname.includes('mobile')) {
      return <>{children}</>;
    }
    return (
      <div className='flex w-screen h-screen overflow-hidden'>
        <Head>
          <meta name='viewport' content='initial-scale=1.0, width=device-width, maximum-scale=1' />
        </Head>
        {router.pathname !== '/construct/app/extra' && (
          <div className={classNames('transition-[width]', isMenuExpand ? 'w-60' : 'w-20', 'hidden', 'md:block')}>
            <SideBar />
          </div>
        )}
        <div className='flex flex-col flex-1 relative overflow-hidden'>{children}</div>
        <FloatHelper />
      </div>
    );
  };

  return (
    <ConfigProvider
      locale={i18n.language === 'en' ? enUS : zhCN}
      theme={{
        token: {
          colorPrimary: '#0C75FC',
          borderRadius: 4,
        },
        algorithm: mode === 'dark' ? antdDarkTheme : undefined,
      }}
    >
      <App>{renderContent()}</App>
    </ConfigProvider>
  );
}

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ChatContextProvider>
      <CssWrapper>
        <LayoutWrapper>
          <Component {...pageProps} />
        </LayoutWrapper>
      </CssWrapper>
    </ChatContextProvider>
  );
}

export default MyApp;
