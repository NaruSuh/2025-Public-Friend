import React from 'react';
import { useForm } from 'react-hook-form';
import { Check, X } from 'lucide-react';
import toast from 'react-hot-toast';
import styles from './ApiKeyForm.module.css';

interface ApiKeyFormData {
  keyValue: string;
  label?: string;
}

interface ApiKeyFormProps {
  sourceId: string;
  onSubmit: (data: { sourceId: string; keyValue: string; label?: string }) => void;
  onCancel: () => void;
  isPending?: boolean;
}

export const ApiKeyForm: React.FC<ApiKeyFormProps> = ({
  sourceId,
  onSubmit,
  onCancel,
  isPending = false,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    reset,
  } = useForm<ApiKeyFormData>({
    mode: 'onChange',
    defaultValues: {
      keyValue: '',
      label: '',
    },
  });

  const onFormSubmit = (data: ApiKeyFormData) => {
    if (!data.keyValue.trim()) {
      toast.error('API key cannot be empty');
      return;
    }

    onSubmit({
      sourceId,
      keyValue: data.keyValue.trim(),
      label: data.label?.trim() || 'User Added Key',
    });

    reset();
  };

  const handleCancel = () => {
    reset();
    onCancel();
  };

  return (
    <form className={styles.addKeyForm} onSubmit={handleSubmit(onFormSubmit)}>
      <div className={styles.formGroup}>
        <input
          type="text"
          className={`${styles.keyInput} ${errors.keyValue ? styles.error : ''}`}
          placeholder="Enter API key value..."
          {...register('keyValue', {
            required: 'API key is required',
            minLength: {
              value: 10,
              message: 'API key must be at least 10 characters',
            },
            pattern: {
              value: /^[a-zA-Z0-9_-]+$/,
              message: 'API key contains invalid characters',
            },
          })}
          disabled={isPending}
        />
        {errors.keyValue && <span className={styles.errorMessage}>{errors.keyValue.message}</span>}
      </div>

      <div className={styles.formGroup}>
        <input
          type="text"
          className={styles.labelInput}
          placeholder="Label (optional)"
          {...register('label', {
            maxLength: {
              value: 50,
              message: 'Label must be less than 50 characters',
            },
          })}
          disabled={isPending}
        />
        {errors.label && <span className={styles.errorMessage}>{errors.label.message}</span>}
      </div>

      <div className={styles.formActions}>
        <button type="submit" className={styles.submitBtn} disabled={!isValid || isPending}>
          <Check size={16} />
          {isPending ? 'Saving...' : 'Save'}
        </button>
        <button
          type="button"
          className={styles.cancelBtn}
          onClick={handleCancel}
          disabled={isPending}
        >
          <X size={16} />
          Cancel
        </button>
      </div>
    </form>
  );
};
