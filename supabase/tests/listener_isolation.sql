-- Run against a disposable/staging Supabase database after the migration.
-- Raises on any failed assertion; never leaves test accounts/data behind.
begin;
set local plpgsql.check_asserts = on;
insert into auth.users(id) values
 ('00000000-0000-4000-8000-000000000001'),
 ('00000000-0000-4000-8000-000000000002');

set local role authenticated;
select set_config('request.jwt.claim.sub', '00000000-0000-4000-8000-000000000001', true);
insert into public.listener_profiles(user_id, display_name)
 values (auth.uid(), 'Listener A');
insert into public.listener_show_follows(user_id, show_id) values (auth.uid(), 'nova');
insert into public.listener_episode_state(user_id, episode_id, saved)
 values (auth.uid(), 'episode-isolation-test', true);

-- Own select/update/delete work, and another account cannot insert/read/update/delete.
do $$
declare t text; n integer;
begin
  foreach t in array array['listener_profiles','listener_show_follows','listener_episode_state'] loop
    execute format('select count(*) from public.%I', t) into n;
    assert n = 1, 'Owner cannot read own row';
    execute format('update public.%I set user_id = user_id', t);
    get diagnostics n = row_count;
    assert n = 1, 'Owner cannot update own row';
    begin
      execute format('update public.%I set user_id = %L::uuid', t,
        '00000000-0000-4000-8000-000000000002');
      raise exception 'Owner can transfer a row to another account';
    exception when insufficient_privilege then null; end;
  end loop;
end $$;

select set_config('request.jwt.claim.sub', '00000000-0000-4000-8000-000000000002', true);
do $$
declare t text; n integer;
begin
  foreach t in array array['listener_profiles','listener_show_follows','listener_episode_state'] loop
    execute format('select count(*) from public.%I', t) into n;
    assert n = 0, 'Other account can read private data';
    execute format('update public.%I set user_id = user_id', t);
    get diagnostics n = row_count;
    assert n = 0, 'Other account can update private data';
    execute format('delete from public.%I', t);
    get diagnostics n = row_count;
    assert n = 0, 'Other account can delete private data';
  end loop;
  begin
    insert into public.listener_profiles(user_id) values ('00000000-0000-4000-8000-000000000001');
    raise exception 'Cross-account insert accepted';
  exception when insufficient_privilege then null; end;
  begin
    insert into public.listener_show_follows(user_id, show_id)
      values ('00000000-0000-4000-8000-000000000001', 'fern');
    raise exception 'Cross-account insert accepted';
  exception when insufficient_privilege then null; end;
  begin
    insert into public.listener_episode_state(user_id, episode_id)
      values ('00000000-0000-4000-8000-000000000001', 'other-episode');
    raise exception 'Cross-account insert accepted';
  exception when insufficient_privilege then null; end;
end $$;

set local role anon;
do $$
declare t text;
begin
  foreach t in array array['listener_profiles','listener_show_follows','listener_episode_state'] loop
    assert not has_table_privilege(current_user, 'public.' || t, 'SELECT'), 'Anonymous read granted';
    assert not has_table_privilege(current_user, 'public.' || t, 'INSERT'), 'Anonymous insert granted';
    assert not has_table_privilege(current_user, 'public.' || t, 'UPDATE'), 'Anonymous update granted';
    assert not has_table_privilege(current_user, 'public.' || t, 'DELETE'), 'Anonymous delete granted';
  end loop;
end $$;

set local role authenticated;
select set_config('request.jwt.claim.sub', '00000000-0000-4000-8000-000000000001', true);
do $$
declare t text; n integer;
begin
  foreach t in array array['listener_profiles','listener_show_follows','listener_episode_state'] loop
    execute format('delete from public.%I', t);
    get diagnostics n = row_count;
    assert n = 1, 'Owner cannot delete own row';
  end loop;
end $$;
rollback;
