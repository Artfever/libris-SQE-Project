package com.example.lms.sqe;

import org.pitest.mutationtest.engine.MutationIdentifier;
import org.pitest.mutationtest.engine.gregor.MethodInfo;
import org.pitest.mutationtest.engine.gregor.MethodMutatorFactory;
import org.pitest.mutationtest.engine.gregor.MutationContext;
import org.pitest.reloc.asm.MethodVisitor;
import org.pitest.reloc.asm.Opcodes;

/** Changes the BR-C01 exactly-one selection comparison from one to two. */
public final class ExactlyOneItemMutator implements MethodMutatorFactory {
  @Override
  public MethodVisitor create(MutationContext context, MethodInfo method, MethodVisitor delegate) {
    if (!"borrow".equals(method.getName())) return delegate;
    return new MethodVisitor(Opcodes.ASM9, delegate) {
      @Override
      public void visitInsn(int opcode) {
        if (opcode == Opcodes.LCONST_1) {
          MutationIdentifier id = context.registerMutation(
              ExactlyOneItemMutator.this, "BR-C01: require two selected items instead of one");
          if (context.shouldMutate(id)) {
            super.visitLdcInsn(2L);
            return;
          }
        }
        super.visitInsn(opcode);
      }
    };
  }

  @Override
  public String getGloballyUniqueId() {
    return getClass().getName();
  }

  @Override
  public String getName() {
    return "SQE_EXACTLY_ONE_ITEM";
  }
}
