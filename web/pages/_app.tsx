import { ChatContext, ChatContextProvider } from '@/app/chat-context';
import SideBar from '@/components/layout/side-bar';
// import FloatHelper from '@/new-components/layout/FloatHelper';
import { STORAGE_LANG_KEY, STORAGE_USERINFO_KEY, STORAGE_USERINFO_VALID_TIME_KEY } from '@/utils/constants/index';
import { App, Button, Card, ConfigProvider, Form, Input, MappingAlgorithm, theme } from 'antd';
import enUS from 'antd/locale/en_US';
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
    i18n.changeLanguage?.(window.localStorage.getItem(STORAGE_LANG_KEY) || 'en');
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
  const [isLogin, setIsLogin] = useState(false);
  const [checkingLogin, setCheckingLogin] = useState(true);

  const router = useRouter();

  // Login detection
  const handleAuth = async () => {
    setCheckingLogin(true);
    try {
      const raw = localStorage.getItem(STORAGE_USERINFO_KEY);
      const vtRaw = localStorage.getItem(STORAGE_USERINFO_VALID_TIME_KEY);
      if (raw) {
        const info = JSON.parse(raw || '{}') as { user_id?: string };
        const vt = vtRaw ? Number(vtRaw) : 0;
        // 30 days validity
        const valid = info?.user_id && vt && Date.now() - vt < 30 * 24 * 60 * 60 * 1000;
        setIsLogin(!!valid);
      } else {
        setIsLogin(false);
      }
    } catch {
      setIsLogin(false);
    } finally {
      setCheckingLogin(false);
    }
  };

  useEffect(() => {
    handleAuth();
  }, []);

  const onFinish = (values: { user_id: string; nick_name?: string }) => {
    const user = {
      user_id: values.user_id?.trim(),
      nick_name: values.nick_name?.trim() || values.user_id?.trim(),
      user_channel: 'local',
    };
    localStorage.setItem(STORAGE_USERINFO_KEY, JSON.stringify(user));
    localStorage.setItem(STORAGE_USERINFO_VALID_TIME_KEY, Date.now().toString());
    setIsLogin(true);
  };

  const renderLogin = () => {
    return (
      <div className='w-screen h-screen flex items-center justify-center bg-[rgba(0,0,0,0.02)]'>
        <Card title='Login' className='w-[360px]'>
          <Form layout='vertical' onFinish={onFinish}>
            <Form.Item label='User ID' name='user_id' rules={[{ required: true, message: 'Please input User ID' }]}>
              <Input placeholder='Enter a unique user id' autoFocus />
            </Form.Item>
            <Form.Item label='Nickname' name='nick_name'>
              <Input placeholder='Optional display name' />
            </Form.Item>
            <Form.Item>
              <Button type='primary' htmlType='submit' block>
                Continue
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </div>
    );
  };

  if (checkingLogin) return null;
  if (!isLogin) return renderLogin();

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
        {/* <FloatHelper /> */}
      </div>
    );
  };

  return (
    <ConfigProvider
      locale={enUS}
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
