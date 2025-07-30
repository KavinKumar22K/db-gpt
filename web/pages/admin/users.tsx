import { Button, Card, Table, Modal, Form, Select, message, Space, Tag, Popconfirm } from 'antd';
import { UserOutlined, DatabaseOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role_name: string;
  is_superuser: boolean;
  is_active: boolean;
  last_login?: string;
  gmt_created: string;
}

interface Database {
  name: string;
  type: string;
}

export default function AdminUsersPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [databases, setDatabases] = useState<Database[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userDatabases, setUserDatabases] = useState<string[]>([]);
  const [form] = Form.useForm();

  // Check if user has admin access
  useEffect(() => {
    const checkAdminAccess = async () => {
      try {
        const response = await fetch('/api/v1/auth/me', {
          credentials: 'include',
        });
        
        if (response.ok) {
          const result = await response.json();
          const user = result.data?.user;
          const permissions = result.data?.permissions;
          
          if (!user?.is_superuser && !permissions?.admin) {
            message.error('Admin access required');
            router.push('/');
            return;
          }
        } else {
          router.push('/login');
          return;
        }
      } catch (error) {
        console.error('Admin access check failed:', error);
        router.push('/login');
        return;
      }
      
      // Load initial data
      loadUsers();
      loadDatabases();
    };

    checkAdminAccess();
  }, [router]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/auth/users', {
        credentials: 'include',
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setUsers(result.data.users);
        }
      }
    } catch (error) {
      console.error('Failed to load users:', error);
      message.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const loadDatabases = async () => {
    try {
      const response = await fetch('/api/v1/chat/db/list', {
        credentials: 'include',
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setDatabases(result.data || []);
        }
      }
    } catch (error) {
      console.error('Failed to load databases:', error);
    }
  };

  const loadUserDatabases = async (userId: number) => {
    try {
      const response = await fetch(`/api/v1/auth/database-access?user_id=${userId}`, {
        credentials: 'include',
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setUserDatabases(result.data.databases);
        }
      }
    } catch (error) {
      console.error('Failed to load user databases:', error);
    }
  };

  const handleManageDatabases = (user: User) => {
    setSelectedUser(user);
    setModalVisible(true);
    loadUserDatabases(user.id);
  };

  const handleGrantAccess = async (values: { databases: string[] }) => {
    if (!selectedUser) return;

    try {
      const promises = values.databases.map(dbName =>
        fetch('/api/v1/auth/database-access/grant', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            user_id: selectedUser.id,
            db_name: dbName,
          }),
        })
      );

      await Promise.all(promises);
      message.success('Database access granted successfully');
      loadUserDatabases(selectedUser.id);
      form.resetFields();
    } catch (error) {
      console.error('Failed to grant database access:', error);
      message.error('Failed to grant database access');
    }
  };

  const handleRevokeAccess = async (dbName: string) => {
    if (!selectedUser) return;

    try {
      const response = await fetch('/api/v1/auth/database-access/revoke', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          user_id: selectedUser.id,
          db_name: dbName,
        }),
      });

      if (response.ok) {
        message.success('Database access revoked successfully');
        loadUserDatabases(selectedUser.id);
      } else {
        message.error('Failed to revoke database access');
      }
    } catch (error) {
      console.error('Failed to revoke database access:', error);
      message.error('Failed to revoke database access');
    }
  };

  const columns = [
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: User) => (
        <Space>
          <UserOutlined />
          {text}
          {record.is_superuser && <Tag color="red">Super Admin</Tag>}
        </Space>
      ),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Full Name',
      dataIndex: 'full_name',
      key: 'full_name',
    },
    {
      title: 'Role',
      dataIndex: 'role_name',
      key: 'role_name',
      render: (role: string) => (
        <Tag color={role === 'admin' ? 'red' : 'blue'}>{role}</Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Last Login',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (date: string) => date ? new Date(date).toLocaleString() : 'Never',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: User) => (
        <Space>
          <Button
            type="link"
            icon={<DatabaseOutlined />}
            onClick={() => handleManageDatabases(record)}
          >
            Manage DB Access
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <Space>
            <UserOutlined />
            User Management
          </Space>
        }
        extra={
          <Button type="primary" onClick={loadUsers}>
            Refresh
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
        />
      </Card>

      <Modal
        title={`Manage Database Access - ${selectedUser?.username}`}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setSelectedUser(null);
          setUserDatabases([]);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <div style={{ marginBottom: 16 }}>
          <h4>Current Database Access:</h4>
          <Space wrap>
            {userDatabases.map(dbName => (
              <Tag
                key={dbName}
                closable
                onClose={() => handleRevokeAccess(dbName)}
                color="blue"
              >
                {dbName}
              </Tag>
            ))}
            {userDatabases.length === 0 && (
              <span style={{ color: '#999' }}>No database access granted</span>
            )}
          </Space>
        </div>

        <Form form={form} onFinish={handleGrantAccess} layout="vertical">
          <Form.Item
            name="databases"
            label="Grant Access to Databases"
            rules={[{ required: true, message: 'Please select databases' }]}
          >
            <Select
              mode="multiple"
              placeholder="Select databases to grant access"
              options={databases
                .filter(db => !userDatabases.includes(db.name))
                .map(db => ({
                  label: `${db.name} (${db.type})`,
                  value: db.name,
                }))
              }
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<PlusOutlined />}>
              Grant Access
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
} 