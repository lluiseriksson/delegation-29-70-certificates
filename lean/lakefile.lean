import Lake
open Lake DSL

package «downward_delegation» where
  leanOptions := #[
    ⟨`autoImplicit, false⟩
  ]

@[default_target]
lean_lib «DownwardDelegation» where
  roots := #[`DownwardDelegation]
