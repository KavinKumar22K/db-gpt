import { Button, Card, Form, Input, message, Tabs } from 'antd';
import { LockOutlined, MailOutlined, UserOutlined } from '@ant-design/icons';
import { useRouter } from 'next/router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { apiInterceptors } from '@/client/api';
import { STORAGE_USERINFO_KEY, STORAGE_USERINFO_VALID_TIME_KEY } from '@/utils/constants';

interface LoginForm {
  username: string;
  password: string;
}

interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  full_name?: string;
}

export default function LoginPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('login');

  const handleLogin = async (values: LoginForm) => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      });

      const result = await response.json();

      if (result.success && result.data?.success) {
        const { user, session_id } = result.data;
        
        // Store user info and session
        localStorage.setItem(STORAGE_USERINFO_KEY, JSON.stringify(user));
        localStorage.setItem(STORAGE_USERINFO_VALID_TIME_KEY, Date.now().toString());
        
        // Set session cookie
        if (session_id) {
          document.cookie = `dbgpt_auth_session=${session_id}; path=/; max-age=${30 * 24 * 60 * 60}`;
        }

        message.success(t('Login successful'));
        
        // Redirect to home page or intended page
        const redirectTo = router.query.redirect as string || '/';
        router.push(redirectTo);
      } else {
        message.error(result.data?.message || t('Login failed'));
      }
    } catch (error) {
      console.error('Login error:', error);
      message.error(t('Login failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: RegisterForm) => {
    if (values.password !== values.confirmPassword) {
      message.error(t('Passwords do not match'));
      return;
    }

    setLoading(true);
    try {
      const { confirmPassword, ...registerData } = values;
      
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registerData),
      });

      const result = await response.json();

      if (result.success && result.data?.success) {
        message.success(t('Registration successful, please login'));
        setActiveTab('login');
      } else {
        message.error(result.data?.message || t('Registration failed'));
      }
    } catch (error) {
      console.error('Registration error:', error);
      message.error(t('Registration failed'));
    } finally {
      setLoading(false);
    }
  };

  const loginForm = (
    <Form
      name="login"
      onFinish={handleLogin}
      size="large"
      autoComplete="off"
    >
      <Form.Item
        name="username"
        rules={[{ required: true, message: t('Please input your username!') }]}
      >
        <Input
          prefix={<UserOutlined />}
          placeholder={t('Username')}
        />
      </Form.Item>

      <Form.Item
        name="password"
        rules={[{ required: true, message: t('Please input your password!') }]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder={t('Password')}
        />
      </Form.Item>

      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          loading={loading}
          style={{ width: '100%' }}
        >
          {t('Login')}
        </Button>
      </Form.Item>
    </Form>
  );

  const registerForm = (
    <Form
      name="register"
      onFinish={handleRegister}
      size="large"
      autoComplete="off"
    >
      <Form.Item
        name="username"
        rules={[
          { required: true, message: t('Please input your username!') },
          { min: 3, message: t('Username must be at least 3 characters') },
        ]}
      >
        <Input
          prefix={<UserOutlined />}
          placeholder={t('Username')}
        />
      </Form.Item>

      <Form.Item
        name="email"
        rules={[
          { required: true, message: t('Please input your email!') },
          { type: 'email', message: t('Please enter a valid email!') },
        ]}
      >
        <Input
          prefix={<MailOutlined />}
          placeholder={t('Email')}
        />
      </Form.Item>

      <Form.Item
        name="full_name"
      >
        <Input
          prefix={<UserOutlined />}
          placeholder={t('Full Name (Optional)')}
        />
      </Form.Item>

      <Form.Item
        name="password"
        rules={[
          { required: true, message: t('Please input your password!') },
          { min: 8, message: t('Password must be at least 8 characters') },
        ]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder={t('Password')}
        />
      </Form.Item>

      <Form.Item
        name="confirmPassword"
        rules={[
          { required: true, message: t('Please confirm your password!') },
        ]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder={t('Confirm Password')}
        />
      </Form.Item>

      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          loading={loading}
          style={{ width: '100%' }}
        >
          {t('Register')}
        </Button>
      </Form.Item>
    </Form>
  );

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }}>
      <Card
        style={{
          width: 400,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        }}
        bodyStyle={{ padding: '32px' }}
      >
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, fontWeight: 'bold', margin: 0 }}>
            DB-GPT
          </h1>
          <p style={{ color: '#666', margin: '8px 0 0' }}>
            {t('Welcome to DB-GPT')}
          </p>
        </div>

        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          centered
          items={[
            {
              key: 'login',
              label: t('Login'),
              children: loginForm,
            },
            {
              key: 'register',
              label: t('Register'),
              children: registerForm,
            },
          ]}
        />
      </Card>
    </div>
  );
} 