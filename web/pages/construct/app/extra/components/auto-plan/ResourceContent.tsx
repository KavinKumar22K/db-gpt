import { apiInterceptors, getResource } from '@/client/api';
import { useRequest } from 'ahooks';
import { Form, Select, Switch } from 'antd';
import cls from 'classnames';
import React, { useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';

const ResourceContent: React.FC<{
  uid: string;
  initValue: any;
  updateData: (data: any) => void;
  classNames?: string;
  resourceTypeOptions: Record<string, any>[];
  setCurIcon: React.Dispatch<
    React.SetStateAction<{
      uid: string;
      icon: string;
    }>
  >;
}> = ({ uid, initValue, updateData, classNames, resourceTypeOptions, setCurIcon }) => {
  const [form] = Form.useForm();
  const type = Form.useWatch('type', form);
  const isDynamic = Form.useWatch('is_dynamic', form);
  const value = Form.useWatch('value', form);
  const { t } = useTranslation();
  // Resource Type Options
  const options = useMemo(() => {
    return resourceTypeOptions?.filter(item => item.value !== 'all') || [];
  }, [resourceTypeOptions]);

  // Get non-dynamic situations，knowledge base、database、Plugin、Orchestrate workflow parameter list
  const { run, data, loading } = useRequest(
    async type => {
      const [, res] = await apiInterceptors(getResource({ type }));
      form.setFieldsValue({
        value: initValue?.value || res?.[0]?.key,
      });
      return res || [];
    },
    {
      manual: true,
    },
  );

  useEffect(() => {
    if (type) {
      run(type);
    }
  }, [run, type]);

  // Dynamic parametersvalueOptions
  const dynamicOptions = useMemo(() => {
    return (
      data?.map(item => {
        return {
          ...item,
          label: item.label,
          value: item.key + '',
        };
      }) || []
    );
  }, [data]);

  // Parameters change dynamically according to the selected resource type
  const renderParameter = () => {
    if (type === 'image_file') {
      return null;
      // return (
      //   <Form.Item label="Upload pictures：" name="value" valuePropName="fileList" required>
      //     <Upload listType="picture-card">
      //       <button style={{ border: 0, background: 'none' }} type="button">
      //         <PlusOutlined />
      //         <div style={{ marginTop: 8 }}>Upload icon</div>
      //       </button>
      //     </Upload>
      //   </Form.Item>
      // );
    }
    if (type === 'internet') {
      return null;
      // return (
      //   <Form.Item label={returnLabel('internet', 'xxx')} name="value">
      //     <Switch style={{ background: value ? '#1677ff' : '#ccc' }} />
      //   </Form.Item>
      // );
    }
    if (['text_file', 'excel_file'].includes(type)) {
      return null;
      // return (
      //   <Form.Item label="Upload file：" name="value" required valuePropName="fileList">
      //     <Upload>
      //       <Button icon={<UploadOutlined />}>Upload file</Button>
      //     </Upload>
      //   </Form.Item>
      // );
    }
    return (
      <Form.Item label={t('resource_value')} name='value' required>
        <Select
          placeholder={t('please_select_param')}
          options={dynamicOptions}
          loading={loading}
          className='w-3/5'
          allowClear
        />
      </Form.Item>
    );
  };

  useEffect(() => {
    const rawVal = form.getFieldsValue();
    // If the dynamictrue，Clear it manually hereDynamic parametersvalue
    const value = rawVal?.is_dynamic ? '' : rawVal?.value;
    updateData({ uid, ...rawVal, value });
  }, [uid, isDynamic, form, updateData, value, type]);

  return (
    <div className={cls('flex flex-1', classNames)}>
      <Form
        style={{ width: '100%' }}
        form={form}
        labelCol={{ span: 4 }}
        initialValues={{
          ...initValue,
        }}
      >
        <Form.Item label={t('resource_type')} name='type'>
          <Select
            className='w-2/5'
            options={options}
            onChange={(val: string) => {
              setCurIcon({ uid, icon: val });
            }}
          />
        </Form.Item>
        <Form.Item label={t('resource_dynamic')} name='is_dynamic'>
          <Switch style={{ background: isDynamic ? '#1677ff' : '#ccc' }} />
        </Form.Item>
        {/* If dynamic parameters are selected, there is no need for parameters here */}
        {!isDynamic && <> {renderParameter()}</>}
      </Form>
    </div>
  );
};
export default ResourceContent;
