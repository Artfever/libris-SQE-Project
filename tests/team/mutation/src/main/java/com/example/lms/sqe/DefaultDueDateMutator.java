package com.example.lms.sqe;

import org.pitest.mutationtest.engine.MutationIdentifier;
import org.pitest.mutationtest.engine.gregor.MethodInfo;
import org.pitest.mutationtest.engine.gregor.MethodMutatorFactory;
import org.pitest.mutationtest.engine.gregor.MutationContext;
import org.pitest.reloc.asm.MethodVisitor;
import org.pitest.reloc.asm.Opcodes;

/** Changes the BR-C05 default loan period from fourteen to thirteen days. */
public final class DefaultDueDateMutator implements MethodMutatorFactory {
  @Override
  public MethodVisitor create(MutationContext context, MethodInfo method, MethodVisitor delegate) {
    if (!"borrow".equals(method.getName())) return delegate;
    return new MethodVisitor(Opcodes.ASM9, delegate) {
      @Override
      public void visitLdcInsn(Object value) {
        if (Long.valueOf(14L).equals(value)) {
          MutationIdentifier id = context.registerMutation(
              DefaultDueDateMutator.this, "BR-C05: default due date uses thirteen days");
          if (context.shouldMutate(id)) {
            super.visitLdcInsn(13L);
            return;
          }
        }
        super.visitLdcInsn(value);
      }
    };
  }

  @Override
  public String getGloballyUniqueId() {
    return getClass().getName();
  }

  @Override
  public String getName() {
    return "SQE_DEFAULT_DUE_DATE";
  }
}
